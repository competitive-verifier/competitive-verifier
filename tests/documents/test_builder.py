from pathlib import Path
import shutil

import pytest

from competitive_verifier import git
from competitive_verifier.documents.builder import load_static_files
from competitive_verifier.documents.type import SiteRenderConfig


@pytest.mark.skipif(
    shutil.which("git") is None, reason="docs subcommand requires git command"
)
def test_load_static_files():
    config = SiteRenderConfig(
        config_yml={"foo": 1},
        destination_dir=Path("foo"),
        index_md=Path(__file__),
        static_dir=Path(__file__),
    )
    d = load_static_files(config=config)
    files = {
        p.relative_to("src/competitive_verifier_resources/jekyll")
        for p in git.ls_files("src/competitive_verifier_resources/jekyll")
    }
    files.add(Path("_config.yml"))

    for f in files:
        print(f.as_posix())

    expected = {"foo" / f for f in files}
    assert set(d.keys()) == expected
