import abc
import enum
import functools
import itertools
import json
import pathlib
import shutil
from collections import defaultdict
from collections.abc import Sequence
from enum import Enum
from logging import getLogger
from typing import Any, Literal

from pydantic import BaseModel

import competitive_verifier.oj.verify.shlex2 as shlex
from competitive_verifier.exec import command_stdout
from competitive_verifier.oj.verify.models import (
    Language,
    LanguageEnvironment,
    OjVerifyLanguageConfig,
)
from competitive_verifier.util import read_text_normalized

# ruff: noqa: PLR2004

logger = getLogger(__name__)

_metadata_by_manifest_path: dict[pathlib.Path, dict[str, Any]] = {}
_cargo_checked_workspaces: set[pathlib.Path] = set()
_related_source_files_by_workspace: dict[
    pathlib.Path, dict[pathlib.Path, frozenset[pathlib.Path]]
] = {}


class OjVerifyRustListDependenciesBackend(BaseModel):
    kind: Literal["none", "cargo-udeps"]
    toolchain: str | None = None


class OjVerifyRustConfig(OjVerifyLanguageConfig):
    list_dependencies_backend: OjVerifyRustListDependenciesBackend | None = None


class _ListDependenciesBackend:
    @abc.abstractmethod
    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        raise NotImplementedError


class _NoBackend(_ListDependenciesBackend):
    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        return _list_dependencies_by_crate(
            path, basedir=basedir, cargo_udeps_toolchain=None
        )


class _CargoUdeps(_ListDependenciesBackend):
    toolchain: str = "nightly"

    def __init__(self, *, toolchain: str | None):
        if toolchain is not None:
            self.toolchain = toolchain

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        return _list_dependencies_by_crate(
            path, basedir=basedir, cargo_udeps_toolchain=self.toolchain
        )


@functools.cache
def _list_dependencies_by_crate(
    path: pathlib.Path, *, basedir: pathlib.Path, cargo_udeps_toolchain: str | None
) -> list[pathlib.Path]:
    """The `list_dependencies` implementation for `_NoBackend` and `CargoUdeps`.

    Args:
        path (pathlib.Path): A main source file path of a target
        basedir (pathlib.Path): A parameter from `Language.list_dependencies`
        cargo_udeps_toolchain (str | None): If not `None`, use `cargo-udeps` with the specified toolchain to detect unused dependencies
    Returns:
        list[pathlib.Path]: A list of dependent `.rs` file paths
    Raises:
        RuntimeError: If any cargo command fails
    """
    path = basedir / path

    # We regard that a generated file does not depend on any files.
    for parent in path.parents:
        if (parent.parent / "Cargo.toml").exists() and parent.parts[-1] == "target":
            logger.warning("This is a generated file!: %s", path)
            return [path]

    metadata = _cargo_metadata(cwd=path.parent)

    # First, collects source files in the same crate.
    common_result = set(
        _source_files_in_same_targets(path, _related_source_files(basedir, metadata))
    )

    main_package_and_target = _find_target(metadata, path)
    if not main_package_and_target:
        return sorted(common_result)
    main_package, main_target = main_package_and_target

    packages_by_id = {p["id"]: p for p in metadata["packages"]}

    class DependencyNamespace(Enum):
        NORMAL_DEVELOPMENT = enum.auto()
        BUILD = enum.auto()

        @classmethod
        def from_dep_kind(cls, kind: str):
            if kind == "build":
                return cls.BUILD
            return cls.NORMAL_DEVELOPMENT

    # Collect the `(|dev-|build-)dependencies` into a <is a `build-dependency`> → (<"extern crate name"> → <package>) dictionary.
    dependencies: defaultdict[DependencyNamespace, dict[str, dict[str, Any]]] = (
        defaultdict(dict)
    )
    for dep in next(
        n["deps"] for n in metadata["resolve"]["nodes"] if n["id"] == main_package["id"]
    ):
        if _need_dev_deps(main_target) or any(
            k["kind"] is None for k in dep["dep_kinds"]
        ):
            dependencies[DependencyNamespace.NORMAL_DEVELOPMENT][dep["name"]] = (
                packages_by_id[dep["pkg"]]
            )
        if any(k["kind"] == "build" for k in dep["dep_kinds"]):
            dependencies[DependencyNamespace.BUILD][dep["name"]] = packages_by_id[
                dep["pkg"]
            ]

    # If `cargo_udeps_toolchain` is present, collects packages that are "unused" by `target`.
    unused_packages: defaultdict[DependencyNamespace, set[Any]] = defaultdict(set)
    if cargo_udeps_toolchain is not None:
        explicit_names_in_toml = {
            (DependencyNamespace.from_dep_kind(d["kind"]), d["rename"])
            for d in main_package["dependencies"]
            if d["rename"]
        }
        if not shutil.which("cargo-udeps"):
            raise RuntimeError("`cargo-udeps` not in $PATH")
        args: list[str] = [
            "rustup",
            "run",
            cargo_udeps_toolchain,
            "cargo",
            "udeps",
            "--output",
            "json",
            "--manifest-path",
            main_package["manifest_path"],
            *_target_option(main_target),
        ]
        unused_deps = json.loads(
            command_stdout(args, cwd=metadata["workspace_root"], check=False)
        )["unused_deps"].values()
        unused_dep = next(
            (
                u
                for u in unused_deps
                if u["manifest_path"] == main_package["manifest_path"]
            ),
            None,
        )
        if unused_dep:
            names_in_toml: list[tuple[DependencyNamespace, Any]] = [
                (DependencyNamespace.NORMAL_DEVELOPMENT, name_in_toml)
                for name_in_toml in [*unused_dep["normal"], *unused_dep["development"]]
            ]
            names_in_toml.extend(
                (DependencyNamespace.BUILD, name_in_toml)
                for name_in_toml in unused_dep["build"]
            )
            for dependency_namespace, name_in_toml in names_in_toml:
                if (dependency_namespace, name_in_toml) in explicit_names_in_toml:
                    # If the `name_in_toml` is explicitly renamed one, it equals to the `extern_crate_name`.
                    unused_package: Any = dependencies[dependency_namespace][
                        name_in_toml
                    ]["id"]
                else:
                    # Otherwise, it equals to the `package.name`.
                    unused_package = next(
                        p["id"]
                        for p in dependencies[dependency_namespace].values()
                        if p["name"] == name_in_toml
                    )
                unused_packages[dependency_namespace].add(unused_package)

    # Finally, adds source files related to the depended crates except:
    #
    # - those detected by cargo-udeps
    # - those come from Crates.io or Git repositories (e.g. `proconio`, other people's libraries including `ac-library-rs`)

    # `main_package` should always be included.
    # Note that cargo-udeps does not detect it if it is unused.
    # https://github.com/est31/cargo-udeps/pull/35
    depended_packages = [main_package]
    for dependency_namespace, values in dependencies.items():
        depended_packages.extend(
            depended_package
            for depended_package in values.values()
            if (
                depended_package["id"] not in unused_packages[dependency_namespace]
                and not depended_package["source"]
            )
        )

    ret = common_result

    for depended_package in depended_packages:
        depended_targets = [
            t
            for t in depended_package["targets"]
            if t != main_target and (_is_build(t) or _is_lib_or_proc_macro(t))
        ]
        assert len(depended_targets) <= 2
        for depended_target in depended_targets:
            related_source_files = _related_source_files(
                basedir,
                _cargo_metadata_by_manifest_path(
                    pathlib.Path(depended_package["manifest_path"])
                ),
            )
            ret |= _source_files_in_same_targets(
                pathlib.Path(depended_target["src_path"]).resolve(strict=True),
                related_source_files,
            )
    return sorted(ret)


def _related_source_files(
    basedir: pathlib.Path, metadata: dict[str, Any]
) -> dict[pathlib.Path, frozenset[pathlib.Path]]:
    """Collects all of the `.rs` files recognized by a workspace.

    Args:
        basedir (pathlib.Path): A parameter from `Language.list_dependencies`
        metadata (dict[str, Any]): "metadata" for a Cargo.toml file in the workspace
    Returns:
        dict[pathlib.Path, frozenset[pathlib.Path]]: A (main source file) → (other related files) map
    Raises:
        RuntimeError: If any cargo command fails
    """
    if pathlib.Path(metadata["workspace_root"]) in _related_source_files_by_workspace:
        return _related_source_files_by_workspace[
            pathlib.Path(metadata["workspace_root"])
        ]

    # Runs `cargo check` to generate `$target_directory/debug/deps/*.d`.
    if pathlib.Path(metadata["workspace_root"]) not in _cargo_checked_workspaces:
        command_stdout(
            [
                "cargo",
                "check",
                "--manifest-path",
                str(pathlib.Path(metadata["workspace_root"], "Cargo.toml")),
                "--workspace",
                "--all-targets",
            ],
            cwd=metadata["workspace_root"],
        )
        _cargo_checked_workspaces.add(pathlib.Path(metadata["workspace_root"]))

    ret: dict[pathlib.Path, frozenset[pathlib.Path]] = {}

    targets_in_workspace = itertools.chain.from_iterable(
        p["targets"]
        for p in metadata["packages"]
        if p["id"] in metadata["workspace_members"]
    )
    for target in targets_in_workspace:
        # Finds the **latest** "dep-info" file that contains a line in the following format, and parses the line.
        #
        # ```
        # <relative/absolute path to the `.d` file itself>: <relative/absolute path to the root source file> <relative/aboslute paths to the other related files>...
        # ```
        #
        # - https://github.com/rust-lang/cargo/blob/rust-1.49.0/src/cargo/core/compiler/fingerprint.rs#L1979-L1997
        # - https://github.com/rust-lang/cargo/blob/rust-1.49.0/src/cargo/core/compiler/fingerprint.rs#L1824-L1830
        if _is_build(target):
            dep_info_paths = pathlib.Path(
                metadata["target_directory"], "debug", "build"
            ).rglob(f"{_crate_name(target)}-*.d")
        elif _is_example(target):
            dep_info_paths = pathlib.Path(
                metadata["target_directory"], "debug", "examples"
            ).glob(f"{_crate_name(target)}-*.d")
        else:
            dep_info_paths = pathlib.Path(
                metadata["target_directory"], "debug", "deps"
            ).glob(f"{_crate_name(target)}-*.d")
        for dep_info_path in sorted(
            dep_info_paths, key=lambda p: p.stat().st_mtime_ns, reverse=True
        ):
            dep_info = read_text_normalized(dep_info_path)
            for line in dep_info.splitlines():
                ss = line.split(": ")
                if (
                    len(ss) == 2
                    and pathlib.Path(metadata["workspace_root"], ss[0]) == dep_info_path
                ):
                    paths: list[pathlib.Path] = []
                    it = iter(ss[1].split())
                    for s in it:
                        ss = s
                        while ss.endswith("\\"):
                            ss = ss.rstrip("\\") + " " + next(it)
                        path = pathlib.Path(metadata["workspace_root"], s).resolve(
                            strict=True
                        )
                        # Ignores paths that don't start with the `basedir`. (e.g. `/dev/null`, `/usr/local/share/foo/bar`)
                        if path.is_relative_to(basedir):
                            paths.append(path)
                    if paths[:1] == [
                        pathlib.Path(target["src_path"]).resolve(strict=True)
                    ]:
                        ret[paths[0]] = frozenset(paths[1:])
                        break
            else:
                continue
            break
        else:
            logger.error("no `.d` file for `%s`", target["name"])

    _related_source_files_by_workspace[pathlib.Path(metadata["workspace_root"])] = ret
    return ret


def _source_files_in_same_targets(
    path: pathlib.Path,
    related_source_files: dict[pathlib.Path, frozenset[pathlib.Path]],
) -> frozenset[pathlib.Path]:
    """Returns `.rs` file paths relating to `path`.

    Args:
        path (pathlib.Path): A main source file path of a target
        related_source_files (dict[pathlib.Path, frozenset[pathlib.Path]]): A (main source file) → (other related files) map
    Returns:
        frozenset[pathlib.Path]: A set of `.rs` file paths relating to `path`
    Raises:
        RuntimeError: If `path` is not found in `related_source_files` and is not related to any other files.
    """
    # If `p` is `src_path` of a target, it does not belong to any other target unless it's weirdly symlinked,
    if path in related_source_files:
        return frozenset({path, *related_source_files[path]})

    # Otherwise, it may be used by multiple targets with `#[path = ".."] mod foo;` or something.
    return frozenset(
        itertools.chain.from_iterable(
            {k, *v} for (k, v) in related_source_files.items() if path in v
        )
    ) or frozenset({path})


class RustLanguageEnvironment(LanguageEnvironment):
    @property
    def name(self) -> str:
        return "Rust"

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str | None:
        path = basedir / path
        metadata = _cargo_metadata(cwd=path.parent)
        target = _ensure_target(metadata, path)
        return f"cd {path.parent.resolve()!s} && " + shlex.join(
            ["cargo", "build", "--release", *_target_option(target)]
        )

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        path = basedir / path
        metadata = _cargo_metadata(cwd=path.parent)
        target = _ensure_target(metadata, path)
        return str(
            pathlib.Path(
                metadata["target_directory"],
                "release",
                *([] if _is_bin(target) else ["examples"]),
                target["name"],
            )
        )


class RustLanguage(Language):
    _list_dependencies_backend: _ListDependenciesBackend

    def __init__(self, *, config: OjVerifyRustConfig | None):
        if config and config.list_dependencies_backend:
            list_dependencies_backend = config.list_dependencies_backend

            if list_dependencies_backend.kind == "none":
                self._list_dependencies_backend = _NoBackend()
            elif list_dependencies_backend.kind == "cargo-udeps":
                self._list_dependencies_backend = _CargoUdeps(
                    toolchain=list_dependencies_backend.toolchain,
                )
            else:
                raise RuntimeError(
                    "expected 'none' or 'cargo-udeps' for `languages.rust.list_dependencies_backend.kind`"
                )
        else:
            self._list_dependencies_backend = _NoBackend()

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        return self._list_dependencies_backend.list_dependencies(path, basedir=basedir)

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[RustLanguageEnvironment]:
        return [RustLanguageEnvironment()]


def _cargo_metadata(cwd: pathlib.Path) -> dict[str, Any]:
    """Returns "metadata" for a Cargo.toml file in `cwd` or its parent directories.

    Args:
        cwd (pathlib.Path): The current working directory
    Returns:
        dict[str, Any]: Output of `cargo metadata` command
    Raises:
        ValueError: If `cwd` is not absolute or contains `..`
        RuntimeError: If no `Cargo.toml` is found
    """
    if not cwd.is_absolute() or ".." in cwd.parts:
        raise ValueError(
            f"the `cwd` parameter must be absolute and must not contain `..`: {cwd}"
        )

    # https://docs.rs/cargo/0.49.0/src/cargo/util/important_paths.rs.html#6-20
    for directory in [cwd, *cwd.parents]:
        manifest_path = directory / "Cargo.toml"
        if manifest_path.exists():
            return _cargo_metadata_by_manifest_path(manifest_path)
    raise RuntimeError(
        f"could not find `Cargo.toml` in `{cwd}` or any parent directory"
    )


def _cargo_metadata_by_manifest_path(manifest_path: pathlib.Path) -> dict[str, Any]:
    """Returns "metadata" for a certain `Cargo.toml`.

    Args:
        manifest_path (pathlib.Path): Path to a `Cargo.toml`
    Returns:
        dict[str, Any]: Output of `cargo metadata` command
    Raises:
        RuntimeError: If the `cargo metadata` command fails
    """
    if manifest_path in _metadata_by_manifest_path:
        return _metadata_by_manifest_path[manifest_path]

    metadata = _run_cargo_metadata(manifest_path)
    root_manifest_path = pathlib.Path(metadata["workspace_root"], "Cargo.toml")
    if root_manifest_path != manifest_path:
        metadata = _run_cargo_metadata(root_manifest_path)

    for key in [
        root_manifest_path,
        *(
            pathlib.Path(p["manifest_path"])
            for p in metadata["packages"]
            if p["id"] in metadata["workspace_members"]
        ),
    ]:
        _metadata_by_manifest_path[key] = metadata

    return metadata


def _run_cargo_metadata(manifest_path: pathlib.Path) -> dict[str, Any]:
    """Runs `cargo metadata` for a certain `Cargo.toml`.

    This function is considered to be executed just once for every Cargo.toml in the repository.
    For detailed information about `cargo metadata`, see:

    - <https://doc.rust-lang.org/cargo/commands/cargo-metadata.html#output-format>
    - <https://docs.rs/cargo_metadata>

    Args:
        manifest_path (pathlib.Path): Path to a `Cargo.toml`
    Returns:
        dict[str, Any]: Output of `cargo metadata` command
    Raises:
        RuntimeError: If the `cargo metadata` command fails
    """
    return json.loads(
        command_stdout(
            [
                "cargo",
                "metadata",
                "--format-version",
                "1",
                "--manifest-path",
                str(manifest_path),
            ],
            cwd=manifest_path.parent,
        )
    )


def _find_target(
    metadata: dict[str, Any],
    src_path: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for package in metadata["packages"]:
        for target in package["targets"]:
            # A `src_path` may contain `..`
            # The path may not actually exist by being excluded from the package.
            if pathlib.Path(target["src_path"]).resolve() == src_path:
                return package, target
    return None


def _ensure_target(metadata: dict[str, Any], src_path: pathlib.Path) -> dict[str, Any]:
    package_and_target = _find_target(metadata, src_path)
    if not package_and_target:
        raise RuntimeError(f"{src_path} is not a main source file of any target")
    _, target = package_and_target
    return target


def _crate_name(target: dict[str, Any]) -> bool:
    return target["name"].replace("-", "_")


def _is_build(target: dict[str, Any]) -> bool:
    return target["kind"] == ["custom-build"]


def _is_lib_or_proc_macro(target: dict[str, Any]) -> bool:
    return target["kind"] in [["lib"], ["proc-macro"]]


def _is_bin(target: dict[str, Any]) -> bool:
    return target["kind"] == ["bin"]


def _is_example(target: dict[str, Any]) -> bool:
    return target["kind"] == ["example"]


def _need_dev_deps(target: dict[str, Any]) -> bool:
    # Comes from https://docs.rs/cargo/0.49.0/cargo/ops/enum.CompileFilter.html#method.need_dev_deps
    return not (_is_lib_or_proc_macro(target) or _is_bin(target))


def _target_option(target: dict[str, Any]) -> list[str]:
    if target["kind"] == ["bin"]:
        return ["--bin", target["name"]]
    if target["kind"] == ["example"]:
        return ["--example", target["name"]]
    if target["kind"] == ["test"]:
        return ["--test", target["name"]]
    if target["kind"] == ["bench"]:
        return ["--bench", target["name"]]
    return ["--lib"]
