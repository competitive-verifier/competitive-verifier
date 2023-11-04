from typing import Any

from competitive_verifier_oj_clone.config import OjVerifyConfig
from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage


class GoLanguage(UserDefinedLanguage):
    config: dict[str, Any]

    def __init__(self, *, config: OjVerifyConfig):
        lang_config = config["languages"].get("go", {})
        assert lang_config is not None
        lang_config.setdefault("execute", "env GO111MODULE=off go run {basedir}/{path}")
        super().__init__(extension="go", config=lang_config)
