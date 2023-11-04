from typing import Any

from competitive_verifier_oj_clone.config import OjVerifyConfig
from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage


class HaskellLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: OjVerifyConfig):
        lang_confg = config["languages"].get("haskell", {})
        assert lang_confg is not None
        lang_confg.setdefault("execute", "runghc {basedir}/{path}")
        super().__init__(extension="hs", config=lang_confg)
