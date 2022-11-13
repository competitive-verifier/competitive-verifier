from typing import Any, Optional

from onlinejudge_verify.config import get_config
from onlinejudge_verify.languages.user_defined import UserDefinedLanguage


class GoLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: Optional[dict[str, Any]] = None):
        if config is None:
            config = get_config().get("languages", {}).get("go", {})
        assert config is not None
        config.setdefault("compile", "echo")
        config.setdefault("execute", "go run {basedir}/{path}")
        super().__init__(extension="go", config=config)
