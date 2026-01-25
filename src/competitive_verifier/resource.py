import sys
from logging import getLogger

logger = getLogger(__name__)


def ulimit_stack() -> None:
    """Run `ulimit -s unlimited`."""
    if sys.platform != "win32":  # pragma: no cover
        import resource  # noqa: PLC0415

        _, hard = resource.getrlimit(resource.RLIMIT_STACK)
        resource.setrlimit(resource.RLIMIT_STACK, (hard, hard))


def try_ulimit_stack() -> None:
    """Run `ulimit -s unlimited` and ignore any errors."""
    try:
        ulimit_stack()
    except Exception:  # noqa: BLE001
        logger.warning("failed to increase the stack size[ulimit]")
