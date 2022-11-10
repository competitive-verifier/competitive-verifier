import pathlib

from .file import VerificationInput


class DependencyResolver:
    input: VerificationInput
    excluded_files: set[pathlib.Path]

    depends_on: dict[pathlib.Path, set[pathlib.Path]]
    required_by: dict[pathlib.Path, set[pathlib.Path]]
    verified_with: dict[pathlib.Path, set[pathlib.Path]]

    def __init__(
        self,
        input: VerificationInput,
        excluded_files: set[pathlib.Path],
    ) -> None:
        self.input = input
        self.excluded_files = excluded_files
        self.depends_on = filter_edge(self.input.depends_on, excluded_files)
        self.required_by = filter_edge(self.input.required_by, excluded_files)
        self.verified_with = filter_edge(self.input.verified_with, excluded_files)


def filter_edge(
    edges: dict[pathlib.Path, set[pathlib.Path]],
    excluded: set[pathlib.Path],
) -> dict[pathlib.Path, set[pathlib.Path]]:
    d: dict[pathlib.Path, set[pathlib.Path]] = {}
    for p, s in edges.items():
        if p not in excluded:
            d[p] = s - excluded
    return d
