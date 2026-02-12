import pathlib

import competitive_verifier_resources


def test_doc_usage():
    doc_usage = competitive_verifier_resources.doc_usage(
        markdown_dir_path=pathlib.Path(),
        repo_name="example/myrepo",
    )
    assert "jekyll serve" in doc_usage
    assert "{{" not in doc_usage


def test_jekyll_files():
    assert "Gemfile" in competitive_verifier_resources.jekyll_files()

    for content in competitive_verifier_resources.jekyll_files().values():
        assert len(content) > 0
