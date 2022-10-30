import pathlib
import competitive_verifier.console.app as app


def test_parse_args_default():
    parsed = app.parse_args(None)
    assert parsed.config_file == pathlib.Path(
        '.competitive-verifier/config.toml')
