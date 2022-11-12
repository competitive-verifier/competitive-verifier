import pathlib

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
    def __init__(self) -> None:
        pass

    def resolve(self) -> VerificationInput:
        files: dict[pathlib.Path, VerificationFile] = {}
        basedir = pathlib.Path.cwd()

        lib_tasks = set[pathlib.Path]()
        for path in git.ls_files("*.test.*"):
            language = onlinejudge_verify.languages.list.get(path)
            if language is None or not language.is_verification_file(
                path, basedir=basedir
            ):
                continue

            deps = list(
                git.ls_files(*language.list_dependencies(path, basedir=basedir))
            )
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
            lib_tasks.update(deps)

        lib_tasks -= files.keys()
        while lib_tasks:
            path = lib_tasks.pop()
            assert path not in files

            language = onlinejudge_verify.languages.list.get(path)
            if language is None:
                continue

            deps = list(
                git.ls_files(*language.list_dependencies(path, basedir=basedir))
            )
            attr = language.list_attributes(path, basedir=basedir)

            files[path] = VerificationFile(
                dependencies=deps,
                document_attributes=attr,
            )
            lib_tasks.update(deps)
            lib_tasks -= files.keys()
        return VerificationInput(files=files)
