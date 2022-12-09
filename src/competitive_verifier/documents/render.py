import importlib.resources
import os
import pathlib
from logging import getLogger
from typing import Any, Optional

import yaml

from competitive_verifier import git, github

from .. import config as conf
from .type import SiteRenderConfig

_RESOURCE_PACKAGE = "competitive_verifier_resources"
_CONFIG_YML_PATH = "_config.yml"

COMPETITIVE_VERIFY_DOCS_CONFIG_YML = "COMPETITIVE_VERIFY_DOCS_CONFIG_YML"

logger = getLogger(__name__)


def _get_default_docs_dir() -> pathlib.Path:
    default_docs_dir = conf.config_dir / "docs"
    oj_verify_docs_dir = pathlib.Path(".verify-helper/docs")
    if not default_docs_dir.exists() and oj_verify_docs_dir.exists():
        return oj_verify_docs_dir
    return default_docs_dir


def _load_user_render_config_yml(docs_dir: pathlib.Path) -> Optional[dict[str, Any]]:
    env_config_yml = os.getenv(COMPETITIVE_VERIFY_DOCS_CONFIG_YML)
    if env_config_yml:
        print(env_config_yml)
        try:
            user_config_yml = yaml.safe_load(env_config_yml)
            if isinstance(user_config_yml, dict):
                return user_config_yml  # type:ignore
            else:
                logger.error("failed to parse $COMPETITIVE_VERIFY_DOCS_CONFIG_YML")
        except Exception as e:
            logger.exception(
                "failed to parse $COMPETITIVE_VERIFY_DOCS_CONFIG_YML: %s",
                e,
            )

    user_config_yml_path = docs_dir / _CONFIG_YML_PATH
    if user_config_yml_path.exists():
        try:
            user_config_yml = yaml.safe_load(user_config_yml_path.read_bytes())
            if isinstance(user_config_yml, dict):
                return user_config_yml  # type:ignore
            else:
                logger.error("failed to parse %s: %s", user_config_yml_path.as_posix())
        except Exception as e:
            logger.exception(
                "failed to parse %s: %s", user_config_yml_path.as_posix(), e
            )


def load_render_config(
    *,
    docs_dir: Optional[pathlib.Path],
    destination_dir: pathlib.Path,
) -> SiteRenderConfig:
    # load default _config.yml
    default_config_yml = yaml.safe_load(
        (importlib.resources.files(_RESOURCE_PACKAGE) / _CONFIG_YML_PATH).read_bytes()
    )
    assert default_config_yml is not None

    config_yml: dict[str, Any] = default_config_yml
    if not docs_dir:
        docs_dir = _get_default_docs_dir()

    logger.info("docs_dir=%s", docs_dir.as_posix())
    user_config_yml = _load_user_render_config_yml(docs_dir)
    if user_config_yml:
        config_yml.update(user_config_yml)

    config_yml.setdefault("action_name", github.env.get_workflow_name())
    config_yml.setdefault("branch_name", github.env.get_ref_name())

    git_root = git.get_root_directory().resolve()
    basedir = pathlib.Path.cwd().relative_to(git_root).as_posix()
    if basedir.startswith("."):
        basedir = ""
    else:
        basedir = f"{basedir}/"
    config_yml.setdefault("basedir", basedir)

    static_dir = docs_dir / "static"
    index_md_path = docs_dir / "index.md"
    return SiteRenderConfig(
        config_yml=config_yml,
        static_dir=static_dir.resolve(),
        index_md=index_md_path.resolve(),
        destination_dir=destination_dir.resolve(),
    )
