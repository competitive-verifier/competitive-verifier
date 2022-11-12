# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false
# Python Version: 3.x
import concurrent.futures
import functools
import pathlib
import platform
import sys
from logging import getLogger
from typing import Any, Sequence

import importlab.environment
import importlab.fs
import importlab.graph

import onlinejudge_verify.shlex2 as shlex
from onlinejudge_verify.languages.models import Language, LanguageEnvironment

logger = getLogger(__name__)


class PythonLanguageEnvironment(LanguageEnvironment):
    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join(
            [
                "oj-verify-python-compile",
                "--path",
                str(path.resolve()),
                "--basedir",
                str(basedir.resolve()),
                "--output",
                str(tempdir.resolve() / "compiled.py"),
            ]
        )

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join([sys.executable, str(tempdir / "compiled.py")])


@functools.lru_cache(maxsize=None)
def _python_list_depending_files(
    path: pathlib.Path, basedir: pathlib.Path
) -> list[pathlib.Path]:
    # compute the dependency graph of the `path`
    env = importlab.environment.Environment(
        importlab.fs.Path([importlab.fs.OSFileSystem(str(basedir.resolve()))]),
        (sys.version_info.major, sys.version_info.minor),
    )
    try:
        executor = concurrent.futures.ThreadPoolExecutor()
        future = executor.submit(
            importlab.graph.ImportGraph.create, env, [str(path)]  # type: ignore
        )
        if platform.uname().system == "Windows":
            timeout = 5.0  # 1.0 sec causes timeout on CI using Windows
        else:
            timeout = 1.0
        res_graph = future.result(timeout=timeout)
    except concurrent.futures.TimeoutError as e:
        raise RuntimeError(
            f"Failed to analyze the dependency graph (timeout): {path}"
        ) from e
    try:
        node_deps_pairs: list[tuple[str, list[str]]] = res_graph.deps_list()
    except Exception as e:
        raise RuntimeError(
            f"Failed to analyze the dependency graph (circular imports?): {path}"
        ) from e
    logger.debug("the dependency graph of %s: %s", str(path), node_deps_pairs)

    # collect Python files which are depended by the `path` and under `basedir`
    res_deps: list[pathlib.Path] = []
    res_deps.append(path.resolve())
    for node_, deps_ in node_deps_pairs:
        node = pathlib.Path(node_)
        deps = list(map(pathlib.Path, deps_))
        if node.resolve() == path.resolve():
            for dep in deps:
                if basedir.resolve() in dep.resolve().parents:
                    res_deps.append(dep.resolve())
            break
    return list(set(res_deps))


class PythonLanguage(Language):
    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        return _python_list_depending_files(path.resolve(), basedir)

    def bundle(
        self, path: pathlib.Path, *, basedir: pathlib.Path, options: dict[str, Any]
    ) -> bytes:
        """
        :throws NotImplementedError:
        """
        raise NotImplementedError

    def is_verification_file(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> bool:
        return ".test.py" in path.name

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[PythonLanguageEnvironment]:
        # TODO add another environment (e.g. pypy)
        return [PythonLanguageEnvironment()]
