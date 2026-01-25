import pathlib

from charset_normalizer import from_bytes


def to_relative(path: pathlib.Path) -> pathlib.Path | None:
    try:
        return path.resolve().relative_to(pathlib.Path.cwd())
    except ValueError:
        return None


def read_text_normalized(path: pathlib.Path) -> str:
    return normalize_bytes_text(path.read_bytes())


def normalize_bytes_text(b: bytes) -> str:
    return str(from_bytes(b).best())
