import pathlib
from abc import ABC
from typing import Any

from ..types import ConfigDirSetter, FilePaths


class IntegrationData(ABC):
    conf_path: pathlib.Path
    file_paths: FilePaths

    def __init__(self, set_config_dir: ConfigDirSetter, file_paths: FilePaths) -> None:
        self.conf_path = set_config_dir(self.name)
        self.file_paths = file_paths

    @classmethod
    @property
    def name(cls) -> str:
        return cls.__name__

    def assert_extra(self):
        pass

    def check_envinronment(self) -> bool:
        return True

    def expected(self) -> dict[str, Any]:
        ...
