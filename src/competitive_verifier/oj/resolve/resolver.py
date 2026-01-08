import fnmatch
import hashlib
import os
import pathlib
import traceback
from argparse import ArgumentParser
from collections.abc import Generator
from functools import cached_property
from itertools import chain
from logging import getLogger
from typing import Any, Literal

from pydantic import Field, ValidationError

from competitive_verifier import config, git, oj
from competitive_verifier.arg import IncludeExcludeArguments, VerboseArguments
from competitive_verifier.models import (
    AddtionalSource,
    CommandVerification,
    ConstVerification,
    ProblemVerification,
    ResultStatus,
    Verification,
    VerificationFile,
    VerificationInput,
)
from competitive_verifier.oj.verify.list import OjVerifyConfig
from competitive_verifier.oj.verify.models import LanguageEnvironment

logger = getLogger(__name__)


def _get_bundled_dir() -> pathlib.Path:
    return config.get_config_dir() / "bundled"


def _write_bundled(content: bytes, *, path: pathlib.Path) -> pathlib.Path:
    """Write bundled code.

    Returns:
        output file path.
    """
    dest_dir = _get_bundled_dir()
    dest_path = dest_dir / path
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("bundle_path=%s", dest_path.as_posix())
    dest_path.write_bytes(content)
    return dest_path


class OjResolver:
    include: list[str]
    exclude: list[str]
    config: OjVerifyConfig
    _match_exclude_cache: dict[pathlib.Path, bool]

    def __init__(
        self,
        *,
        include: list[str],
        exclude: list[str],
        config: OjVerifyConfig,
    ) -> None:
        def _remove_slash(s: str):
            s = os.path.normpath(s)
            while len(s) > 1 and s[-1] == os.sep:
                s = s[:-1]
            return s

        self.include = list(map(_remove_slash, include))
        self.exclude = list(map(_remove_slash, exclude))
        self.config = config
        self._match_exclude_cache = {}

    def _match_exclude2(self, paths: list[pathlib.Path]) -> bool:
        if not paths:
            return False
        path = paths.pop()
        cache = self._match_exclude_cache.get(path, None)
        if cache is not None:
            return cache

        for ex in self.exclude:
            if fnmatch.fnmatch(path.as_posix(), ex):
                self._match_exclude_cache[path] = True
                return True
        result = self._match_exclude2(paths)
        self._match_exclude_cache[path] = result
        return result

    def _match_exclude(self, path: pathlib.Path) -> bool:
        paths = list(path.parents)
        paths.reverse()
        paths.append(path)
        return self._match_exclude2(paths)

    @cached_property
    def _lang_dict(self):
        return self.config.get_dict()

    @staticmethod
    def env_to_verifications(
        env: LanguageEnvironment,
        *,
        attr: dict[str, Any],
        path: pathlib.Path,
        basedir: pathlib.Path,
    ) -> Generator[Verification, None, None]:
        if "IGNORE" in attr:
            yield ConstVerification(status=ResultStatus.SKIPPED)
            return

        error_str = attr.get("ERROR")
        try:
            error = float(error_str) if error_str else None
        except ValueError:
            error = None

        tle_str = attr.get("TLE")
        tle = float(tle_str) if tle_str else None

        mle_str = attr.get("MLE")
        mle = float(mle_str) if mle_str else None

        url = attr.get("PROBLEM")

        if url:
            tempdir = oj.get_directory(url)
            yield ProblemVerification(
                name=env.name,
                command=env.get_execute_command(path, basedir=basedir, tempdir=tempdir),
                compile=env.get_compile_command(path, basedir=basedir, tempdir=tempdir),
                problem=url,
                error=error,
                tle=tle,
                mle=mle,
            )

        if attr.get("STANDALONE") is not None:
            tempdir = (
                config.get_cache_dir()
                / "standalone"
                / hashlib.md5(
                    path.as_posix().encode("utf-8"), usedforsecurity=False
                ).hexdigest()
            )
            yield CommandVerification(
                name=env.name,
                command=env.get_execute_command(path, basedir=basedir, tempdir=tempdir),
                compile=env.get_compile_command(path, basedir=basedir, tempdir=tempdir),
                tempdir=tempdir,
            )

        unit_test_envvar = attr.get("UNITTEST")
        if unit_test_envvar:
            var = os.getenv(unit_test_envvar)
            if var is None:
                logger.warning(
                    "UNITTEST envvar %s is not defined.",
                    unit_test_envvar,
                )
                yield ConstVerification(status=ResultStatus.FAILURE)
            elif var.lower() == "false" or var == "0":
                logger.info(
                    "UNITTEST envvar %s=%s is falsy.",
                    unit_test_envvar,
                    var,
                )
                yield ConstVerification(status=ResultStatus.FAILURE)
            else:
                logger.info(
                    "UNITTEST envvar %s=%s is truthy.",
                    unit_test_envvar,
                    var,
                )
                yield ConstVerification(status=ResultStatus.SUCCESS)

    def resolve(self, *, bundle: bool) -> VerificationInput:
        files: dict[pathlib.Path, VerificationFile] = {}
        basedir = pathlib.Path.cwd()

        for path in git.ls_files(*self.include):
            if self._match_exclude(path):
                logger.debug("exclude=%s", path.as_posix())
                continue

            language = self._lang_dict.get(path.suffix)
            if language is None:
                continue

            deps = set(git.ls_files(*language.list_dependencies(path, basedir=basedir)))
            attr = language.list_attributes(path, basedir=basedir)

            additonal_sources: list[AddtionalSource] = []
            if bundle:
                try:
                    bundled_code = language.bundle(path, basedir=basedir)
                    if bundled_code:
                        dest_path = _write_bundled(bundled_code, path=path)
                        additonal_sources.append(
                            AddtionalSource(name="bundled", path=dest_path)
                        )
                except Exception:  # noqa: BLE001
                    dest_path = _write_bundled(
                        traceback.format_exc().encode(), path=path
                    )
                    additonal_sources.append(
                        AddtionalSource(name="bundle error", path=dest_path)
                    )

            verifications = list(
                chain.from_iterable(
                    self.env_to_verifications(vs, attr=attr, path=path, basedir=basedir)
                    for vs in language.list_environments(path, basedir=basedir)
                )
            )
            files[path] = VerificationFile(
                dependencies=deps,
                verification=verifications,
                document_attributes=attr,
                additonal_sources=additonal_sources,
            )
        return VerificationInput(files=files)


class OjResolve(IncludeExcludeArguments, VerboseArguments):
    subcommand: Literal["oj-resolve"] = Field(
        default="oj-resolve",
        description="Create verify_files json using `oj-verify`",
    )
    bundle: bool = True
    config: pathlib.Path | OjVerifyConfig | None = None

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "--no-bundle",
            dest="bundle",
            action="store_false",
            help="Disable bundle",
        )
        parser.add_argument(
            "--config",
            help="config.toml",
            type=pathlib.Path,
        )

    def to_resolver(self) -> OjResolver:
        if self.config is None:
            logger.info("no config file")
            config = OjVerifyConfig()
        elif not isinstance(self.config, OjVerifyConfig):
            try:
                config_path = self.config
                with pathlib.Path(config_path).open("rb") as fp:
                    config = OjVerifyConfig.load(fp)
                    logger.info("config file loaded: %s: %s", str(config_path), config)
            except ValidationError:
                logger.exception("config file validation error")
                config = OjVerifyConfig()
        else:
            config = self.config

        return OjResolver(
            include=self.include,
            exclude=self.exclude,
            config=config,
        )

    def _run(self) -> bool:
        logger.debug("arguments:%s", self)
        resolved = self.to_resolver().resolve(bundle=self.bundle)
        print(resolved.model_dump_json(exclude_none=True))
        return True
