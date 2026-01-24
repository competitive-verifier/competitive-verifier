import os
import pathlib
import re


def is_in_github_actions() -> bool:
    return os.getenv("GITHUB_ACTIONS", "").lower() == "true"


def get_ref_name() -> str | None:
    return os.getenv("GITHUB_REF_NAME")


def get_repository() -> str | None:
    return os.getenv("GITHUB_REPOSITORY")


def get_workflow_name() -> str | None:
    return os.getenv("GITHUB_WORKFLOW")


def get_workflow_ref() -> str | None:
    return os.getenv("GITHUB_WORKFLOW_REF")


def get_workflow_filename() -> str | None:
    ref = get_workflow_ref()
    if not ref:
        return None
    return re.sub(r".*/([^/]+\.yml)@.*$", r"\1", ref)


def _optional_path(strpath: str | None) -> pathlib.Path | None:
    return pathlib.Path(strpath) if strpath else None


def get_step_summary_path() -> pathlib.Path | None:
    return _optional_path(os.getenv("GITHUB_STEP_SUMMARY"))
