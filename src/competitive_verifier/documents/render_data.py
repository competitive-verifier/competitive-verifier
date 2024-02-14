import datetime
import enum
from typing import Annotated, Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, PlainSerializer, model_validator
from pydantic.alias_generators import to_camel

from competitive_verifier.models import ForcePosixPath, SortedPathList, TestcaseResult


class StatusIcon(str, enum.Enum):
    @property
    def is_failed(self) -> bool:
        return not self.is_success

    @property
    def is_success(self) -> bool:
        return (
            self == self.LIBRARY_ALL_AC
            or self == self.LIBRARY_PARTIAL_AC
            or self == self.LIBRARY_NO_TESTS
            or self == self.TEST_ACCEPTED
            or self == self.TEST_WAITING_JUDGE
        )

    @property
    def is_test(self) -> bool:
        return not self.is_library

    @property
    def is_library(self) -> bool:
        return (
            self == self.LIBRARY_ALL_AC
            or self == self.LIBRARY_PARTIAL_AC
            or self == self.LIBRARY_SOME_WA
            or self == self.LIBRARY_ALL_WA
            or self == self.LIBRARY_NO_TESTS
        )

    LIBRARY_ALL_AC = "LIBRARY_ALL_AC"
    LIBRARY_PARTIAL_AC = "LIBRARY_PARTIAL_AC"
    LIBRARY_SOME_WA = "LIBRARY_SOME_WA"
    LIBRARY_ALL_WA = "LIBRARY_ALL_WA"
    LIBRARY_NO_TESTS = "LIBRARY_NO_TESTS"
    TEST_ACCEPTED = "TEST_ACCEPTED"
    TEST_WRONG_ANSWER = "TEST_WRONG_ANSWER"
    TEST_WAITING_JUDGE = "TEST_WAITING_JUDGE"


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
    title: Optional[str] = None

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
    environment: Optional[str]


class CategorizedIndex(RenderBaseModel):
    name: str
    pages: list[RenderLink]


class IndexFiles(RenderBaseModel):
    type: str
    categories: list[CategorizedIndex]


class PageRenderData(RenderBaseModel):
    path: ForcePosixPath
    path_extension: str
    title: Optional[str]
    embedded: list[EmbeddedCode]

    timestamp: Annotated[
        datetime.datetime,
        PlainSerializer(lambda x: str(x), return_type=str, when_used="json"),
    ]
    attributes: dict[str, Any]
    testcases: Optional[list[EnvTestcaseResult]] = None

    is_failed: bool
    is_verification_file: bool
    verification_status: StatusIcon

    depends_on: SortedPathList
    required_by: SortedPathList
    verified_with: SortedPathList

    document_path: Optional[ForcePosixPath] = None
    dependencies: list[Dependency]


class CodePageData(PageRenderData):
    document_content: Optional[str]


class MultiCodePageData(RenderBaseModel):
    path: ForcePosixPath
    verification_status: StatusIcon
    is_failed: bool
    codes: Sequence[CodePageData]
    dependencies: list[Dependency]


class IndexRenderData(RenderBaseModel):
    top: list[IndexFiles]
