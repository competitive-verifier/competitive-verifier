import pathlib

from charset_normalizer import from_bytes


def to_relative(path: pathlib.Path) -> pathlib.Path | None:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd().resolve())
    except ValueError:
        return None


def _resolve_referenced_path_inner(
    target_path: str,
    *,
    basedir: pathlib.Path,
):
    if target_path.startswith(("./", "../")):
        # a relative path
        path = basedir / pathlib.Path(target_path)
        if path.exists():
            return path
    elif target_path.startswith("//"):
        # from the document root
        path = pathlib.Path(target_path[2:])
        if path.exists():
            return path

    path = pathlib.Path(target_path)
    if path.exists():
        return path

    path = basedir / pathlib.Path(target_path)
    if path.exists():
        return path
    return None


def resolve_referenced_path(
    target_path: str,
    *,
    basedir: pathlib.Path,
) -> pathlib.Path | None:
    path = _resolve_referenced_path_inner(target_path, basedir=basedir)
    if path:
        path = path.resolve()
        if path.is_relative_to(pathlib.Path.cwd()):
            return path.relative_to(pathlib.Path.cwd())
    return None


def read_text_normalized(path: pathlib.Path) -> str:
    return normalize_bytes_text(path.read_bytes())


def normalize_bytes_text(b: bytes) -> str:
    return str(from_bytes(b).best())
