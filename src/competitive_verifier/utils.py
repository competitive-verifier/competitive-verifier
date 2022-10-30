
import pathlib
from logging import getLogger

logger = getLogger(__name__)


class VerificationSummary:
    def __init__(self, *, failed_test_paths: list[pathlib.Path]):
        self.failed_test_paths = failed_test_paths

    def show(self) -> None:
        if self.failed_test_paths:
            logger.error(f'{len(self.failed_test_paths)} tests failed')
            for path in self.failed_test_paths:
                logger.error('failed: %s', str(
                    path.resolve().relative_to(pathlib.Path.cwd())
                ))
        else:
            logger.info('all tests succeeded')

    def succeeded(self) -> bool:
        return not self.failed_test_paths
