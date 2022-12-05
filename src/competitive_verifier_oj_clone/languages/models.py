# Python Version: 3.x
import abc
import pathlib
from typing import Any, Optional, Sequence

import competitive_verifier_oj_clone.languages.special_comments as special_comments


class LanguageEnvironment:
    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> Optional[str]:
        """
        :throws Exception:
        """
        return None

    @abc.abstractmethod
    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        raise NotImplementedError


class Language:
    def list_attributes(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> dict[str, Any]:
        """
        :throws Exception:
        """

        attributes: dict[str, Any] = special_comments.list_special_comments(path)
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

    def is_verification_file(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> bool:
        return ".test." in path.name

    @abc.abstractmethod
    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        raise NotImplementedError
