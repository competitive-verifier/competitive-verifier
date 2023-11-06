from typing import Any

import pytest

from competitive_verifier.verify.split_state import SplitState

test_split_by_split_state_params: list[tuple[SplitState, list[Any], list[Any]]] = [
    (SplitState(size=3, index=0), [0, 1, 2, 3, 4], [0]),
    (SplitState(size=3, index=1), [0, 1, 2, 3, 4], [1, 2]),
    (SplitState(size=3, index=2), [0, 1, 2, 3, 4], [3, 4]),
    (SplitState(size=6, index=4), [0, 1, 2, 3, 4], [4]),
    (SplitState(size=6, index=5), [0, 1, 2, 3, 4], []),
    (SplitState(size=3, index=2), ["a", "b", "c", "d", "e"], ["d", "e"]),
]


@pytest.mark.parametrize(
    "state, lst, expected",
    test_split_by_split_state_params,
    ids=range(len(test_split_by_split_state_params)),
)
def test_split_by_split_state(state: SplitState, lst: list[Any], expected: list[Any]):
    assert state.split(lst) == expected
