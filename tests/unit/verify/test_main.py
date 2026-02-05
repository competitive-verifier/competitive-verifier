import pathlib

import pytest

from competitive_verifier import app
from competitive_verifier.models.error import VerifierError
from competitive_verifier.verify import Verify
from competitive_verifier.verify.verifier import SplitState

test_get_split_state_params = [
    (None, None, None),
    (5, 0, SplitState(size=5, index=0)),
    (5, 1, SplitState(size=5, index=1)),
    (5, 2, SplitState(size=5, index=2)),
    (5, 3, SplitState(size=5, index=3)),
    (5, 4, SplitState(size=5, index=4)),
]


@pytest.mark.parametrize(
    ("size", "index", "expected"),
    test_get_split_state_params,
    ids=str,
)
def test_get_split_state(
    size: int | None,
    index: int | None,
    expected: SplitState | None,
):
    v = Verify(
        subcommand="verify",
        verify_files_json=pathlib.Path("verify.json"),
        split=size,
        split_index=index,
    )
    assert v.split_state == expected


get_split_state_error_params = {
    "No split index": (
        ["--verify-json", "verify.json", "--split", "2"],
        "--split argument requires --split-index argument.",
    ),
    "No split": (
        ["--verify-json", "verify.json", "--split-index", "2"],
        "--split-index argument requires --split argument.",
    ),
    "split index": (
        ["--verify-json", "verify.json", "--split-index", "5", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split index negative": (
        ["--verify-json", "verify.json", "--split-index", "-1", "--split", "5"],
        "--split-index must be greater than 0 and less than --split.",
    ),
    "split zero": (
        ["--verify-json", "verify.json", "--split-index", "1", "--split", "0"],
        "--split must be greater than 0.",
    ),
}


@pytest.mark.parametrize(
    ("args", "message"),
    get_split_state_error_params.values(),
    ids=get_split_state_error_params.keys(),
)
def test_get_split_state_error(args: list[str], message: str):
    parsed = app.ArgumentParser().parse(["verify", *args])

    assert isinstance(parsed, app.Verify)

    with pytest.raises(VerifierError) as e:
        _ = parsed.split_state

    assert e.value.message == message
