from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SplitState(BaseModel):
    size: int
    index: int

    def __str__(self) -> str:
        return f"{self.index}/{self.size}"

    def split(self, lst: list[T]) -> list[T]:
        """Split list


        Args:
            lst (list[T]): Target list

        Returns:
            list[T]: Splited list

        Example:
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
        """

        if len(lst) <= self.size:
            if len(lst) <= self.index:
                return []
            else:
                return [lst[self.index]]

        from_index = len(lst) * self.index // self.size
        to_index = len(lst) * (self.index + 1) // self.size
        return lst[from_index:to_index]
