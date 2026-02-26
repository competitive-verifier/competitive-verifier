import os
import pathlib

from pytest_mock import MockerFixture

from competitive_verifier import config


def test_config_dir(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {}, clear=True)

    assert config.get_config_dir() == pathlib.Path(".competitive-verifier")
    assert config.get_cache_dir() == pathlib.Path(".competitive-verifier/cache")
    assert config.get_problem_cache_dir() == pathlib.Path(
        ".competitive-verifier/cache/problems"
    )

    mocker.patch.dict(
        os.environ, {"COMPETITIVE_VERIFY_CONFIG_PATH": "/root/foo"}, clear=True
    )

    assert config.get_config_dir() == pathlib.Path("/root/foo")
    assert config.get_cache_dir() == pathlib.Path("/root/foo/cache")
    assert config.get_problem_cache_dir() == pathlib.Path("/root/foo/cache/problems")
