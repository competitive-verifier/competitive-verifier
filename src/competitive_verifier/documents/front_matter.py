import yaml

from .type import FrontMatter

_separator: bytes = b"---"


def _split_front_matter_without_parsing_yaml(content: bytes) -> tuple[bytes, bytes]:
    lines = content.splitlines(keepends=True)
    if len(lines) == 0 or lines[0].rstrip() != _separator:
        return (b"", content)
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line.rstrip() == _separator:
            break
    else:
        return b"", content

    front_matter = b"".join(lines[1:i])
    content = b"".join(lines[i + 1 :])
    return front_matter, content


def split_front_matter(content: bytes) -> tuple[FrontMatter, bytes]:
    front_matter, content = _split_front_matter_without_parsing_yaml(content)
    return FrontMatter.parse_obj(yaml.safe_load(front_matter) or {}), content


def merge_front_matter(front_matter: FrontMatter, content: bytes) -> bytes:
    if not front_matter:
        return content
    return b"\n".join(
        [
            _separator,
            yaml.safe_dump(front_matter.dict()).rstrip().encode(),
            _separator,
            content,
        ]
    )
