from typing import Any, Optional

from competitive_verifier_oj_clone.config import get_config
from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage


class HaskellLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: Optional[dict[str, Any]] = None):
        if config is None:
            config = get_config()["languages"].get("haskell", {})
        assert config is not None
        config.setdefault("execute", "runghc {basedir}/{path}")
        super().__init__(extension="hs", config=config)
