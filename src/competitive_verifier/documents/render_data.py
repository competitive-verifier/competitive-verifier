import datetime
import enum
from collections.abc import Sequence
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, PlainSerializer, model_validator
from pydantic.alias_generators import to_camel

from competitive_verifier.models import ForcePosixPath, SortedPathList, TestcaseResult


class FileType(enum.Enum):
    LIBRARY = enum.auto()
    TEST = enum.auto()


class StatusIcon(str, enum.Enum):
    def __new__(cls, file_type: FileType, result: str, _: object) -> "StatusIcon":
        value = f"{file_type.name}_{result}"
        member = str.__new__(cls, value)
        member._value_ = value
        return member

    def __init__(self, file_type: FileType, result: str, is_success: bool) -> None:  # noqa: FBT001
        super().__init__()
        self.file_type = file_type
        self.result = result
        self.is_success = is_success

    LIBRARY_ALL_AC = (FileType.LIBRARY, "ALL_AC", True)
    LIBRARY_PARTIAL_AC = (FileType.LIBRARY, "PARTIAL_AC", True)
    LIBRARY_SOME_WA = (FileType.LIBRARY, "SOME_WA", False)
    LIBRARY_ALL_WA = (FileType.LIBRARY, "ALL_WA", False)
    LIBRARY_NO_TESTS = (FileType.LIBRARY, "NO_TESTS", True)
    TEST_ACCEPTED = (FileType.TEST, "ACCEPTED", True)
    TEST_WRONG_ANSWER = (FileType.TEST, "WRONG_ANSWER", False)
    TEST_WAITING_JUDGE = (FileType.TEST, "WAITING_JUDGE", True)

    @property
    def is_failed(self) -> bool:
        return not self.is_success

    @property
    def is_test(self) -> bool:
        return self.file_type == FileType.TEST


class RenderBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
    )


class RenderLink(RenderBaseModel):
    path: ForcePosixPath
    filename: str
    icon: StatusIcon
    title: str | None = None

    @model_validator(mode="after")
    def validate_title(self: "RenderLink") -> "RenderLink":
        if self.path.as_posix() == self.title:
            self.title = None
        return self


class Dependency(RenderBaseModel):
    type: str
    files: list[RenderLink]


class EmbeddedCode(RenderBaseModel):
    name: str
    code: str


class EnvTestcaseResult(RenderBaseModel, TestcaseResult):
    environment: str | None


class CategorizedIndex(RenderBaseModel):
    name: str
    pages: list[RenderLink]


class IndexFiles(RenderBaseModel):
    type: str
    categories: list[CategorizedIndex]


class PageRenderData(RenderBaseModel):
    path: ForcePosixPath
    path_extension: str
    title: str | None
    embedded: list[EmbeddedCode]

    timestamp: Annotated[
        datetime.datetime,
        PlainSerializer(lambda x: str(x), return_type=str, when_used="json"),
    ]
    attributes: dict[str, Any]
    testcases: list[EnvTestcaseResult] | None = None

    is_failed: bool
    is_verification_file: bool
    verification_status: StatusIcon

    depends_on: SortedPathList
    required_by: SortedPathList
    verified_with: SortedPathList

    document_path: ForcePosixPath | None = None
    dependencies: list[Dependency]


class CodePageData(PageRenderData):
    document_content: str | None


class MultiCodePageData(RenderBaseModel):
    path: ForcePosixPath
    verification_status: StatusIcon
    is_failed: bool
    codes: Sequence[CodePageData]
    dependencies: list[Dependency]


class IndexRenderData(RenderBaseModel):
    top: list[IndexFiles]
