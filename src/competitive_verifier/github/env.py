import os
import pathlib
import re


def _optional_path(strpath: str | None) -> pathlib.Path | None:
    return pathlib.Path(strpath) if strpath else None


def is_in_github_actions() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "true"


def is_enable_debug() -> bool:
    return os.getenv("GITHUB_ACTIONS") == "1"


def get_ref_name() -> str | None:
    return os.getenv("GITHUB_REF_NAME")


def get_api_token() -> str | None:
    return os.getenv("GITHUB_TOKEN")


def get_event_name() -> str | None:
    return os.getenv("GITHUB_EVENT_NAME")


def get_api_url() -> str | None:
    return os.getenv("GITHUB_API_URL")


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


def get_output_path() -> pathlib.Path | None:
    strpath = os.getenv("GITHUB_OUTPUT")
    return _optional_path(strpath)


def get_workspace_path() -> pathlib.Path | None:
    strpath = os.getenv("GITHUB_WORKSPACE")
    return _optional_path(strpath)


def get_step_summary_path() -> pathlib.Path | None:
    strpath = os.getenv("GITHUB_STEP_SUMMARY")
    return _optional_path(strpath)
