import importlib.resources
from logging import getLogger

import yaml

from .. import config as conf
from .type import SiteRenderConfig

_RESOURCE_PACKAGE = "competitive_verifier_resources"
_CONFIG_YML_PATH = "_config.yml"


logger = getLogger(__name__)

docs_dir = conf.config_dir / "docs"
static_dir = docs_dir / "static"
index_md_path = docs_dir / "index.md"
markdown_dir = conf.config_dir / "markdown"


def load_render_config() -> SiteRenderConfig:
    # load default _config.yml
    default_config_yml = yaml.safe_load(
        importlib.resources.read_binary(_RESOURCE_PACKAGE, _CONFIG_YML_PATH)
    )
    assert default_config_yml is not None
    config_yml = default_config_yml

    user_config_yml_path = docs_dir / _CONFIG_YML_PATH
    if user_config_yml_path.exists():
        try:
            with open(user_config_yml_path, "rb") as fh:
                user_config_yml = yaml.safe_load(fh.read())
            assert user_config_yml is not None
        except Exception as e:
            logger.exception(
                "failed to parse %s: %s", user_config_yml_path.as_posix(), e
            )
        else:
            config_yml.update(user_config_yml)

    return SiteRenderConfig(
        config_yml=config_yml,
        static_dir=static_dir.resolve(),
        index_md=index_md_path.resolve(),
        destination_dir=markdown_dir.resolve(),
    )
