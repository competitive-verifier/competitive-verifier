import pathlib
from typing import Annotated, Iterable

from pydantic.functional_serializers import PlainSerializer

ForcePosixPath = Annotated[
    pathlib.Path,
    PlainSerializer(lambda x: x.as_posix(), return_type=str, when_used="json"),
]


def _sorted(items: Iterable[ForcePosixPath]):
    return sorted(items, key=lambda x: str.casefold(x.as_posix()))


SortedPathSet = Annotated[
    set[ForcePosixPath],
    PlainSerializer(_sorted, return_type=list[ForcePosixPath], when_used="json"),
]


SortedPathList = Annotated[
    list[ForcePosixPath],
    PlainSerializer(_sorted, return_type=list[ForcePosixPath]),
]

RelativeDirectoryPath = Annotated[
    pathlib.Path,
    PlainSerializer(
        lambda x: f"{x.as_posix()}/" if x != pathlib.Path(".") else "",
        return_type=str,
        when_used="json",
    ),
]
