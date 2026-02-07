from contextlib import nullcontext
from logging import getLogger

import requests.exceptions

from competitive_verifier import log
from competitive_verifier.models import Problem

from .problem import NotLoggedInError, problem_from_url

logger = getLogger(__name__)


def _run(*, problem: Problem) -> bool:
    try:
        return bool(problem.download_system_cases())
    except requests.exceptions.RequestException:
        logger.exception("Failed to download samples from the server")
        return False


def main(url: str, *, group_log: bool = False) -> bool:
    # prepare values
    problem = problem_from_url(url)
    if problem is None:
        logger.error('The URL "%s" is not supported', url)
        return False

    with (
        log.group(f"download[Run]: {url}")
        if group_log
        else nullcontext(logger.info("download[Run]: %s", url))
    ):
        try:
            _run(problem=problem)
        except Exception as e:
            if isinstance(e, NotLoggedInError):
                logger.exception(*e.args)
            else:
                logger.exception("Failed to download")
            return False
    return True
