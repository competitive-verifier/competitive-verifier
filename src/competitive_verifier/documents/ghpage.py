import json
import os
import pathlib
import urllib.request
from logging import getLogger

import competitive_verifier.github as github

from ..exec import exec_command

logger = getLogger(__name__)


def check_pushed_to_github_head_branch() -> bool:
    if not github.env.is_in_github_actions():
        return False

    # check it is kicked by "push" event
    if github.env.get_event_name() != "push":
        logger.info(
            'This execution is not kicked from "push" event. Updating GitHub Pages is skipped.'
        )
        return False

    # check it is on the default branch.
    try:
        # /repos/{owner}/{repo} endpoint. See https://docs.github.com/en/free-pro-team@latest/rest/reference/repos#get-a-repository

        api_url = github.env.get_api_url()
        repository = github.env.get_reository()

        if not (api_url and repository):
            logger.warning(
                "Failed to get api_url or repository. api_url=%s repository=%s",
                api_url,
                repository,
            )
            logger.info("Updating GitHub Pages is skipped.")
            return False

        repo_api_url = f"{api_url}/repos/{repository}"
        with urllib.request.urlopen(repo_api_url) as fh:
            repos = json.loads(fh.read())
        default_branch = repos["default_branch"]
    except Exception as e:
        logger.exception("Failed to get the default branch: %s", e)
        logger.info("Updating GitHub Pages is skipped.")
        return False
    if github.env.get_branch_or_tag() != f"refs/heads/{default_branch}":
        logger.info(
            'This execution is not on the default branch (the default is "refs/heads/%s" but the actual is "%s"). Updating GitHub Pages is skipped.',
            default_branch,
            github.env.get_branch_or_tag(),
        )
        return False
    return True


def push_documents_to_gh_pages(
    srcdir: pathlib.Path,
    dst_branch: str = "gh-pages",
) -> bool:
    logger.info("upload documents...")

    GH_PAT = os.getenv("GH_PAT")

    # read config
    if not GH_PAT:
        # If we push commits using GITHUB_TOKEN, the build of GitHub Pages will not run. See https://github.com/marketplace/actions/github-pages-deploy#secrets and https://github.com/maxheld83/ghpages/issues/1
        logger.error(
            "GH_PAT is not available. You cannot upload the generated documents to GitHub Pages."
        )
        return False
    logger.info("use GH_PAT")

    repository = github.env.get_reository()
    assert bool(repository)
    logger.info("GITHUB_REPOSITORY = %s", repository)

    url = f"https://{GH_PAT}@github.com/{repository}.git"

    # checkout gh-pages
    logger.info("$ git checkout %s", dst_branch)
    exec_command(["git", "stash", "-u"], check=True)

    if exec_command(["git", "switch", dst_branch], check=False).returncode:
        exec_command(["git", "switch", "--orphan", dst_branch], check=True)

    # # commit and push
    logger.info("$ git add . && git commit && git push")

    if exec_command(["git", "add", srcdir.as_posix()], check=False).returncode:
        logger.info("Not found docs")
        return False

    message = f'[auto-verifier] docs commit {os.getenv("GITHUB_SHA")}'

    name = "GitHub"
    mail = "noreply@github.com"
    git_env = dict(
        os.environ,
        GIT_AUTHOR_NAME=name,
        GIT_COMMITTER_NAME=name,
        GIT_AUTHOR_EMAIL=mail,
        GIT_COMMITTER_EMAIL=mail,
    )

    if exec_command(
        ["git", "commit", "-m", message], check=False, env=git_env
    ).returncode:
        logger.info("Not updated")
        return False

    exec_command(["git", "push", url, "HEAD"], check=True)
    return True
