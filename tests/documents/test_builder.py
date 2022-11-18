from pathlib import Path

from competitive_verifier import git
from competitive_verifier.documents.builder import load_static_files
from competitive_verifier.documents.type import SiteRenderConfig

STATIC_FILES_PATH = "src/competitive_verifier_resources/jekyll"
# For windows test
static_files = git.ls_files(STATIC_FILES_PATH)


def test_load_static_files():
    config = SiteRenderConfig(
        config_yml={"foo": 1},
        destination_dir=Path("foo"),
        index_md=Path(__file__),
        static_dir=Path(__file__),
    )
    d = load_static_files(config=config)
    files = {p.relative_to(STATIC_FILES_PATH) for p in static_files}
    files.add(Path("_config.yml"))

    for f in files:
        print(f.as_posix())

    expected = {"foo" / f for f in files}
    assert set(d.keys()) == expected
