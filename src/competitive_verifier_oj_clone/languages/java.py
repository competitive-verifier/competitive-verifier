import pathlib
from logging import getLogger
from typing import Any, Optional, Sequence

import competitive_verifier_oj_clone.shlex2 as shlex
from competitive_verifier_oj_clone.config import get_config
from competitive_verifier_oj_clone.languages.models import LanguageEnvironment
from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage

logger = getLogger(__name__)


class JavaLanguageEnvironment(LanguageEnvironment):
    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join(["javac", str(basedir / path)])

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        relative_path = (basedir / path).relative_to(basedir)
        class_path = ".".join([*relative_path.parent.parts, relative_path.stem])
        return shlex.join(["java", class_path])


class JavaLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: Optional[dict[str, Any]] = None):
        if config is None:
            config = get_config()["languages"].get("java", {})
        assert config is not None
        if "compile" in config:
            raise RuntimeError('You cannot overwrite "compile" for Java language')
        if "execute" in config:
            raise RuntimeError('You cannot overwrite "execute" for Java language')
        super().__init__(extension="java", config=config)

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        return [JavaLanguageEnvironment()]
