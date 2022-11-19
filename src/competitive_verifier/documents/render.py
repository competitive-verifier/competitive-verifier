import importlib.resources
import os
import pathlib
from functools import lru_cache
from logging import getLogger
from typing import Any, Optional

import yaml

from competitive_verifier import github

from .. import config as conf
from .type import SiteRenderConfig

_RESOURCE_PACKAGE = "competitive_verifier_resources"
_CONFIG_YML_PATH = "_config.yml"

COMPETITIVE_VERIFY_DOCS_CONFIG_YML = "COMPETITIVE_VERIFY_DOCS_CONFIG_YML"

logger = getLogger(__name__)


@lru_cache(maxsize=1)
def get_docs_dir() -> pathlib.Path:
    oj_verify_config_dir = pathlib.Path(".verify-helper")
    if not conf.config_dir.exists() and oj_verify_config_dir.exists():
        config_dir = oj_verify_config_dir
    config_dir = conf.config_dir
    return config_dir / "docs"


def _load_user_render_config_yml() -> Optional[dict[str, Any]]:
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

    docs_dir = get_docs_dir()
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


def load_render_config(*, destination_dir: pathlib.Path) -> SiteRenderConfig:
    # load default _config.yml
    default_config_yml = yaml.safe_load(
        (importlib.resources.files(_RESOURCE_PACKAGE) / _CONFIG_YML_PATH).read_bytes()
    )
    assert default_config_yml is not None

    config_yml: dict[str, Any] = default_config_yml
    user_config_yml = _load_user_render_config_yml()
    if user_config_yml:
        config_yml.update(user_config_yml)

    config_yml.setdefault("action_name", github.env.get_workflow_name())
    config_yml.setdefault("branch_name", github.env.get_ref_name())

    docs_dir = get_docs_dir()
    static_dir = docs_dir / "static"
    index_md_path = docs_dir / "index.md"
    return SiteRenderConfig(
        config_yml=config_yml,
        static_dir=static_dir.resolve(),
        index_md=index_md_path.resolve(),
        destination_dir=destination_dir.resolve(),
    )
