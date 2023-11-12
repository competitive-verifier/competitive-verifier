import pathlib

from competitive_verifier.documents.static_files import default_resource_files


def test_jekyll_staic_files():
    resources = list(default_resource_files())
    src_resources_jekyll_root = (
        pathlib.Path(__file__).parent.parent.parent
        / "src/competitive_verifier_resources/jekyll"
    )
    src_resources_path = list(src_resources_jekyll_root.glob("**/*"))
    src_resources = [
        (p.relative_to(src_resources_jekyll_root).as_posix(), p.read_bytes())
        for p in src_resources_path
        if p.is_file()
    ]
    assert sorted(src_resources, key=lambda r: r[0]) == sorted(
        resources, key=lambda r: r[0]
    )
