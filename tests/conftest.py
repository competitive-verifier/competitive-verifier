import os
from logging import LogRecord
from typing import TypeGuard, TypeVar

import pytest
from pytest_mock import MockerFixture

from tests import LogComparer


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )


def pytest_assertrepr_compare(
    config: pytest.Config,
    op: str,
    left: object,
    right: object,
):
    if op == "==" and _typed_list(left, LogRecord) and _typed_list(right, LogComparer):
        return _asserrepr_log_comparer(config, left, right)
    return None


def _asserrepr_log_comparer(
    config: pytest.Config, left: list[LogRecord], right: list[LogComparer]
) -> list[str] | None:
    size = min(len(left), len(right))
    if size == 0:
        return None
    for i in range(size):
        ll = LogComparer.from_record(left[i])
        left[i] = ll  # pyright: ignore[reportArgumentType, reportCallIssue]
        right[i] = right[i].fill(ll)
    rt = config.hook.pytest_assertrepr_compare(
        config=config, op="==", left=left, right=right
    )
    return rt[0]


TVal = TypeVar("TVal")


def _typed_list(value: object, cls: type[TVal]) -> TypeGuard[list[TVal]]:
    return (
        isinstance(value, list) and all(isinstance(v, cls) for v in value)  # pyright: ignore[reportUnknownVariableType]
    )


@pytest.fixture(autouse=True)
def force_not_github_actions(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": ""})
