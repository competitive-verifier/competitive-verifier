import pathlib
from itertools import chain
from typing import Generator

import competitive_verifier.git as git
import competitive_verifier.oj as oj
import oj_verify_clone.list
from competitive_verifier.models import (
    CommandVerification,
    ProblemVerification,
    Verification,
    VerificationFile,
    VerificationInput,
)
from oj_verify_clone.languages.models import LanguageEnvironment


class OjResolver:
    include: list[pathlib.Path]
    exclude: list[pathlib.Path]

    def __init__(
        self,
        *,
        include: list[pathlib.Path],
        exclude: list[pathlib.Path],
    ) -> None:
        self.include = include
        self.exclude = exclude

    def resolve(self) -> VerificationInput:
        files: dict[pathlib.Path, VerificationFile] = {}
        basedir = pathlib.Path.cwd()

        def to_relative(path: pathlib.Path) -> pathlib.Path:
            if path.is_absolute():
                return path.relative_to(basedir)
            return path

        exclude_paths = set(
            chain.from_iterable(p.glob("**/*") for p in map(to_relative, self.exclude))
        )

        for path in git.ls_files(*self.include):
            if path in exclude_paths:
                continue

            language = oj_verify_clone.list.get(path)
            if language is None:
                continue

            deps = set(git.ls_files(*language.list_dependencies(path, basedir=basedir)))
            attr = language.list_attributes(path, basedir=basedir)

            def env_to_verifications(
                env: LanguageEnvironment,
            ) -> Generator[Verification, None, None]:
                error_str = attr.get("ERROR")
                error = float(error_str) if error_str else None
                url = attr.get("PROBLEM")

                if url:
                    tempdir = oj.get_directory(url)
                    yield ProblemVerification(
                        command=env.get_execute_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        compile=env.get_compile_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        problem=url,
                        error=error,
                    )

                if "UNITTEST" in attr:
                    tempdir = oj.get_random_cache_directory()
                    yield CommandVerification(
                        command=env.get_execute_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
                        compile=env.get_compile_command(
                            path, basedir=basedir, tempdir=tempdir
                        ),
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
            )
        return VerificationInput(files=files)
