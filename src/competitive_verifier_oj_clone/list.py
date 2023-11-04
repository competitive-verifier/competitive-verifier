from competitive_verifier_oj_clone.config import OjVerifyConfig
from competitive_verifier_oj_clone.languages.models import Language


def get_dict(config: OjVerifyConfig) -> dict[str, Language]:
    from competitive_verifier_oj_clone.languages.cplusplus import CPlusPlusLanguage
    from competitive_verifier_oj_clone.languages.go import GoLanguage
    from competitive_verifier_oj_clone.languages.haskell import HaskellLanguage
    from competitive_verifier_oj_clone.languages.java import JavaLanguage
    from competitive_verifier_oj_clone.languages.nim import NimLanguage
    from competitive_verifier_oj_clone.languages.python import PythonLanguage
    from competitive_verifier_oj_clone.languages.ruby import RubyLanguage
    from competitive_verifier_oj_clone.languages.rust import RustLanguage
    from competitive_verifier_oj_clone.languages.user_defined import UserDefinedLanguage

    d: dict[str, Language] = {}
    d[".cpp"] = CPlusPlusLanguage(config=config)
    d[".hpp"] = d[".cpp"]
    d[".cc"] = d[".cpp"]
    d[".h"] = d[".cpp"]
    d[".nim"] = NimLanguage(config=config)
    d[".py"] = PythonLanguage()
    d[".hs"] = HaskellLanguage(config=config)
    d[".ruby"] = RubyLanguage(config=config)
    d[".go"] = GoLanguage(config=config)
    d[".java"] = JavaLanguage(config=config)
    d[".rs"] = RustLanguage(config=config)

    for ext, lang_config in config["languages"].items():
        if "." + ext in d:
            if not isinstance(d["." + ext], UserDefinedLanguage):
                for key in (
                    "compile",
                    "execute",
                    "bundle",
                    "list_attributes",
                    "list_dependencies",
                ):
                    if key in lang_config:
                        raise RuntimeError(
                            "You cannot overwrite existing language: .{}".format(ext)
                        )
        else:
            d["." + ext] = UserDefinedLanguage(extension=ext, config=lang_config)

    return d
