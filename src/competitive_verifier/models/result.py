import datetime
import pathlib
from logging import getLogger
from typing import Any, Optional, Union

PathLike = Union[str, pathlib.Path]
logger = getLogger(__name__)


class FileVerificationResult:
    path: pathlib.Path
    last_success_time: Optional[datetime.datetime]

    def __init__(
        self,
        path: PathLike,
        *,
        last_success_time: Optional[datetime.datetime] = None,
    ):
        self.path = pathlib.Path(path)
        self.last_success_time = last_success_time

    def is_success(self, start_time: datetime.datetime) -> bool:
        return (
            self.last_success_time is not None and self.last_success_time >= start_time
        )


class VerificationResult:
    def __init__(self, *, files: list[FileVerificationResult]):
        self.files = files

    def show_summary(self, start_time: datetime.datetime) -> None:
        failed_results = [r for r in self.files if not r.is_success(start_time)]
        if failed_results:
            logger.error(f"{len(failed_results)} tests failed")
            for r in failed_results:
                logger.error(
                    "failed: %s", str(r.path.resolve().relative_to(pathlib.Path.cwd()))
                )
        else:
            logger.info("all tests succeeded")


def decode_result_json(d: dict[Any, Any]) -> VerificationResult:
    def decode_datetime(s: Optional[str]) -> Optional[datetime.datetime]:
        if s is None:
            return None
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")

    def decode_file_result(d: dict[Any, Any]) -> FileVerificationResult:
        return FileVerificationResult(
            path=d["path"],
            last_success_time=decode_datetime(d.get("last_success_time")),
        )

    return VerificationResult(files=[decode_file_result(x) for x in d["results"]])
