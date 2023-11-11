from competitive_verifier.documents.config import ConfigYaml


def show_default_config_yml():
    print(ConfigYaml().model_dump_yml().decode(encoding="utf-8"))
