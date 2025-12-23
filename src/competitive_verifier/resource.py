import sys


def ulimit_stack() -> None:
    """Run `ulimit -s unlimited`."""
    if sys.platform != "win32":
        import resource

        _, hard = resource.getrlimit(resource.RLIMIT_STACK)
        resource.setrlimit(resource.RLIMIT_STACK, (hard, hard))
