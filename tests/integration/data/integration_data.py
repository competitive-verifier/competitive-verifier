import pathlib
from abc import ABC
from typing import Any, Optional

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
    def config_path(self) -> Optional[str]:
        ...

    @property
    def include_path(self) -> Optional[list[str]]:
        ...

    @property
    def exclude_path(self) -> Optional[list[str]]:
        ...

    def assert_extra(self):
        pass

    def check_envinronment(self) -> bool:
        return True

    def expected_verify_json(self) -> dict[str, Any]:
        ...

    def expected_verify_result(self) -> dict[str, Any]:
        ...
