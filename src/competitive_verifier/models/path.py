import pathlib
from typing import Annotated

from pydantic.functional_serializers import PlainSerializer

ForcePosixPath = Annotated[
    pathlib.Path,
    PlainSerializer(lambda x: x.as_posix(), return_type=str, when_used="json"),
]
