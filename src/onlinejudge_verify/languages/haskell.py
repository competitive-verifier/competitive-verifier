from typing import Any, Optional

from onlinejudge_verify.config import get_config
from onlinejudge_verify.languages.user_defined import UserDefinedLanguage


# TODO: stop using UserDefinedLanguage
class HaskellLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: Optional[dict[str, Any]] = None):
        if config is None:
            config = get_config().get("languages", {}).get("haskell", {})
        assert config is not None
        config.setdefault("compile", "echo")
        config.setdefault("execute", "runghc {basedir}/{path}")
        super().__init__(extension="hs", config=config)
