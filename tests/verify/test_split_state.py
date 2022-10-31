from competitive_verifier.verify.verifier import SplitState


def test_split_by_split_state():
    state = SplitState(size=3, index=0)
    assert state.split([0, 1, 2, 3, 4]) == [0]
    state = SplitState(size=3, index=1)
    assert state.split([0, 1, 2, 3, 4]) == [1, 2]
    state = SplitState(size=3, index=2)
    assert state.split([0, 1, 2, 3, 4]) == [3, 4]
    state = SplitState(size=6, index=4)
    assert state.split([0, 1, 2, 3, 4]) == [4]
    state = SplitState(size=6, index=5)
    assert state.split([0, 1, 2, 3, 4]) == []
