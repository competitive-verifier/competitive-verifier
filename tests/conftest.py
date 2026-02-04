import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )
