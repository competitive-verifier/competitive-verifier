from typing import Any

from competitive_verifier_oj_clone.config import OjVerifyConfig
from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage


class RubyLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: OjVerifyConfig):
        lang_confg = config["languages"].get("ruby", {})
        assert lang_confg is not None
        lang_confg.setdefault("execute", "ruby {basedir}/{path}")
        super().__init__(extension="rb", config=lang_confg)
