# Python Version: 3.x
import abc
import pathlib
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict

from competitive_verifier.models import ShellCommandLike
from competitive_verifier.oj.verify.languages import special_comments


class LanguageEnvironment(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> Optional[ShellCommandLike]:
        """
        :throws Exception:
        """
        return None

    @abc.abstractmethod
    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> ShellCommandLike:
        raise NotImplementedError


class Language:
    def list_attributes(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> dict[str, Any]:
        """
        :throws Exception:
        """

        attributes: dict[str, Any] = dict(special_comments.list_special_comments(path))
        attributes.setdefault("links", [])
        attributes["links"].extend(special_comments.list_embedded_urls(path))
        return attributes

    @abc.abstractmethod
    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        """
        :throws Exception:
        """

        raise NotImplementedError

    def bundle(self, path: pathlib.Path, *, basedir: pathlib.Path) -> Optional[bytes]:
        """
        :throws Exception:
        """
        return None

    @abc.abstractmethod
    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        raise NotImplementedError


class OjVerifyLanguageConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class OjVerifyUserDefinedConfig(OjVerifyLanguageConfig):
    execute: ShellCommandLike
    compile: Optional[ShellCommandLike] = None
    bundle: Optional[ShellCommandLike] = None
    list_attributes: Optional[ShellCommandLike] = None
    list_dependencies: Optional[ShellCommandLike] = None
