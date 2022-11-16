from pathlib import Path
from competitive_verifier import git
from competitive_verifier.documents.builder import load_static_files
from competitive_verifier.documents.type import SiteRenderConfig


def test_load_static_files():
    config = SiteRenderConfig(
        config_yml={"foo": 1},
        destination_dir=Path("foo"),
        index_md=Path(__file__),
        static_dir=Path(__file__),
    )
    d = load_static_files(config=config)

    expected = {
        ("foo" / p.relative_to("src/competitive_verifier_resources/jekyll"))
        for p in git.ls_files("src/competitive_verifier_resources/jekyll")
    }
    expected.add(Path("foo/_config.yml"))

    assert d.keys() == expected
