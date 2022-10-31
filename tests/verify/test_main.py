import argparse
from typing import Optional

import pytest
from competitive_verifier.verify.util import VerifyError

from competitive_verifier.verify.main import argument_verify, get_split_state
from competitive_verifier.verify.verifier import SplitState


get_split_state_params = [
    (None, None, None),
    (5, 0, SplitState(size=5, index=0)),
    (5, 1, SplitState(size=5, index=1)),
    (5, 2, SplitState(size=5, index=2)),
    (5, 3, SplitState(size=5, index=3)),
    (5, 4, SplitState(size=5, index=4)),
]


@pytest.mark.parametrize(
    "size, index, expected",
    get_split_state_params,
    ids=list(f"{tup[1]}/{tup[0]}" for tup in get_split_state_params),
)
def test_get_split_state(
    size: Optional[int],
    index: Optional[int],
    expected: Optional[SplitState],
):
    assert get_split_state(size, index) == expected


get_split_state_error_params = {
    "No split index": (
        ["verify.json", "--split", "2"],
        "--split argument requires --split-index argument.",
    ),
    "No split": (
        ["verify.json", "--split-index", "2"],
        "--split-index argument requires --split argument.",
    ),
    "split index": (
        ["verify.json", "--split-index", "5", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split index negative": (
        ["verify.json", "--split-index", "-1", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split zero": (
        ["verify.json", "--split-index", "1", "--split", "0"],
        "--split must be greater than 0.",
    ),
}


@pytest.mark.parametrize(
    "args, message",
    get_split_state_error_params.values(),
    ids=list(get_split_state_error_params.keys()),
)
def test_get_split_state_error(args: list[str], message: str):
    parser = argument_verify(argparse.ArgumentParser())
    parsed = parser.parse_args(args)

    with pytest.raises(VerifyError) as e:
        get_split_state(parsed.split, parsed.split_index)

    assert e.value.message == message
