import datetime
from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, PlainSerializer, computed_field
from pydantic.alias_generators import to_camel

from competitive_verifier.models.dependency import VerificationStatus
from competitive_verifier.models.path import ForcePosixPath
from competitive_verifier.models.result import TestcaseResult

StatusIcon = Annotated[
    VerificationStatus,
    PlainSerializer(lambda x: x.name, return_type=str, when_used="json"),
]


class BuilderBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class RenderPage(BuilderBaseModel):
    path: ForcePosixPath
    icon: StatusIcon
    title: Optional[str]

    @computed_field
    @property
    def filename(self) -> str:
        return self.path.name


class TopPageCategory(BuilderBaseModel):
    name: str
    pages: list[RenderPage]


class TopPageFiles(BuilderBaseModel):
    type: str
    categories: list[TopPageCategory]


class EmbeddedCode(BuilderBaseModel):
    name: str
    code: str


class EnvTestcaseResult(BuilderBaseModel, TestcaseResult):
    environment: Optional[str]


class Dependency(BuilderBaseModel):
    type: str
    files: list[RenderPage]


class RenderSourceCodeStat(BuilderBaseModel):
    path: ForcePosixPath
    embedded: list[EmbeddedCode]
    is_verification_file: bool
    verification_status: StatusIcon
    timestamp: Annotated[
        datetime.datetime,
        PlainSerializer(lambda x: str(x), return_type=str, when_used="json"),
    ]
    depends_on: list[ForcePosixPath]
    required_by: list[ForcePosixPath]
    verified_with: list[ForcePosixPath]
    attributes: dict[str, Any]
    testcases: Optional[list[EnvTestcaseResult]]


class RenderForPage(RenderSourceCodeStat):
    path_extension: str
    dependencies: list[Dependency]
    is_failed: bool
    verification_status: StatusIcon
    document_path: Optional[ForcePosixPath]

    @classmethod
    def from_source_code_stat(
        cls,
        parent: RenderSourceCodeStat,
        *,
        dependencies: list[Dependency],
    ) -> "RenderForPage":
        return RenderForPage(
            dependencies=dependencies,
            **parent.model_dump(),
        )


class RenderTopPage(BuilderBaseModel):
    top: list[TopPageFiles]
