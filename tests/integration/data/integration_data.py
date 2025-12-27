import pathlib
from abc import ABC, abstractmethod
from typing import Any

import pytest

from ..types import ConfigDirSetter, FilePaths


class IntegrationData(ABC):
    config_dir_path: pathlib.Path
    targets_path: pathlib.Path
    file_paths: FilePaths

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        self.config_dir_path = set_config_dir(self.config_dir_name())
        self.file_paths = file_paths
        self.targets_path = file_paths.root / self.input_name()
        monkeypatch.chdir(self.targets_path)

    @classmethod
    def input_name(cls) -> str:
        return cls.__name__

    @classmethod
    def config_dir_name(cls) -> str:
        return cls.__name__

    @property
    def config_path(self) -> str | None:
        return None

    @property
    def include_path(self) -> list[str] | None:
        return None

    @property
    def exclude_path(self) -> list[str] | None:
        return None

    def assert_extra(self):
        return

    def check_envinronment(self) -> bool:
        return True

    @abstractmethod
    def expected_verify_json(self) -> dict[str, Any]: ...

    @abstractmethod
    def expected_verify_result(self) -> dict[str, Any]: ...
