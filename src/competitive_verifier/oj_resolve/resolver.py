import pathlib
from itertools import chain

import competitive_verifier.git as git
import competitive_verifier.oj as oj
import onlinejudge_verify.languages.list
from competitive_verifier.models import (
    ProblemVerification,
    Verification,
    VerificationFile,
    VerificationInput,
)
from onlinejudge_verify.languages.models import LanguageEnvironment


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

            language = onlinejudge_verify.languages.list.get(path)
            if language is None:
                continue

            deps = set(git.ls_files(*language.list_dependencies(path, basedir=basedir)))
            attr = language.list_attributes(path, basedir=basedir)

            def env_to_verification(env: LanguageEnvironment) -> Verification:
                error_str = attr.get("ERROR")
                error = float(error_str) if error_str else None
                url: str = attr["PROBLEM"]
                tempdir = oj.get_directory(url)
                return ProblemVerification(
                    command=env.get_execute_command(
                        path, basedir=basedir, tempdir=tempdir
                    ),
                    compile=env.get_compile_command(
                        path, basedir=basedir, tempdir=tempdir
                    ),
                    problem=url,
                    error=error,
                )

            verifications = []
            if language.is_verification_file(path, basedir=basedir):
                verifications = list(
                    map(
                        env_to_verification,
                        language.list_environments(path, basedir=basedir),
                    )
                )
            files[path] = VerificationFile(
                dependencies=deps,
                verification=verifications,
                document_attributes=attr,
            )
        return VerificationInput(files=files)
