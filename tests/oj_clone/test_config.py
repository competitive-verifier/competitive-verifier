import pathlib

import competitive_verifier_oj_clone.config as config


def test_oj_resolve_config_load():
    cfg = config.load(pathlib.Path("examples/config.toml"))
    assert cfg is not None
    assert cfg["languages"] == {
        "awk": {
            "bundle": "false",
            "compile": "bash -c 'echo hello > {tempdir}/hello'",
            "execute": "env AWKPATH={basedir} awk -f {path}",
            "list_dependencies": "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' "
            "{path}",
        },
        "txt": {
            "bundle": "false",
            "compile": "true",
            "execute": "true",
            "list_dependencies": "",
        },
    }
