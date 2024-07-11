import fnmatch
import hashlib
import os
import pathlib
import traceback
from functools import cached_property
from itertools import chain
from logging import getLogger
from typing import Generator

import competitive_verifier.config as config
import competitive_verifier.git as git
import competitive_verifier.oj as oj
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


def get_bundled_dir() -> pathlib.Path:
    return config.get_config_dir() / "bundled"


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

            def env_to_verifications(
                env: LanguageEnvironment,
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
                        command=env.get_execute_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        compile=env.get_compile_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        problem=url,
                        error=error,
                        tle=tle,
                        mle=mle,
                    )

                if attr.get("STANDALONE") is not None:
                    tempdir = (
                        config.get_cache_dir()
                        / "standalone"
                        / hashlib.md5(path.as_posix().encode("utf-8")).hexdigest()
                    )
                    yield CommandVerification(
                        name=env.name,
                        command=env.get_execute_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        compile=env.get_compile_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
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

            additonal_sources: list[AddtionalSource] = []
            if bundle:
                try:
                    bundled_code = language.bundle(path, basedir=basedir)
                    if bundled_code:
                        dest_dir = get_bundled_dir()
                        dest_path = dest_dir / path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        logger.info("bundle_path=%s", dest_path.as_posix())
                        dest_path.write_bytes(bundled_code)
                        additonal_sources.append(
                            AddtionalSource(name="bundled", path=dest_path)
                        )
                except Exception:
                    bundled_code = traceback.format_exc()
                    dest_dir = get_bundled_dir()
                    dest_path = dest_dir / path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.info("bundle_path=%s", dest_path.as_posix())
                    dest_path.write_text(bundled_code, encoding="utf-8")
                    additonal_sources.append(
                        AddtionalSource(name="bundle error", path=dest_path)
                    )

            verifications = list(
                chain.from_iterable(
                    env_to_verifications(vs)
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
