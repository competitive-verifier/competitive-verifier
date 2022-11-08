import importlib.resources
import pathlib
from itertools import chain
from logging import getLogger

import yaml

import competitive_verifier_resources
from competitive_verifier import git, github
from competitive_verifier.models import VerificationInput, VerifyCommandResult

from .. import config as conf
from .page import check_pushed_to_github_head_branch, push_documents_to_gh_pages
from .type import SiteRenderConfig

logger = getLogger(__name__)

docs_dir = conf.config_dir / "docs"
static_dir = docs_dir / "static"
index_md_path = docs_dir / "index.md"
markdown_dir = conf.config_dir / "markdown"


_RESOURCE_PACKAGE = competitive_verifier_resources
_CONFIG_YML_PATH = "_config.yml"
_DOC_USAGE_PATH = "doc_usage.txt"


class DocumentBuilder:
    input: VerificationInput
    result: VerifyCommandResult

    def __init__(self, input: VerificationInput, result: VerifyCommandResult) -> None:
        self.input = input
        self.result = result

    def build(self) -> bool:
        logger.info("Generate documents...")
        result = self.impl()
        logger.info("Generated.")

        if github.env.is_in_github_actions():
            workspace = github.env.get_workspace_path()
            assert workspace is not None
            if pathlib.Path.cwd().resolve() != workspace.resolve():
                logger.warning(
                    "Working directory should be git root. " "Working directory: %s",
                    pathlib.Path.cwd().as_posix(),
                )
                result = False
            elif check_pushed_to_github_head_branch():
                # Push gh-pages when in GitHub head branch
                if not push_documents_to_gh_pages(srcdir=markdown_dir):
                    result = False
        else:
            logger.info(
                importlib.resources.read_text(
                    _RESOURCE_PACKAGE, _DOC_USAGE_PATH
                ).replace("{{{{{markdown_dir_path}}}}}", markdown_dir.as_posix())
            )

        return result

    def impl(self) -> bool:
        config = load_render_config()
        logger.debug("lender config=%s", config)

        excluded_files = set(
            chain.from_iterable(
                ex.glob("**/*")
                for ex in map(pathlib.Path, config.config_yml.get("exclude", []))
            )
        )
        logger.debug(
            "excluded_files=%s",
            " ".join(p.as_posix() for p in excluded_files),
        )

        markdown_paths = set(
            p
            for p in git.ls_files()
            if p.suffix == ".md"
            and not p.name.startswith(".")
            and p not in excluded_files
        )
        logger.debug(
            "markdown_paths=%s",
            " ".join(p.as_posix() for p in markdown_paths),
        )

        logger.info("list rendering jobs...")
        import sys

        sys.exit()
        return False


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


def get_markdown_paths(*, basedir: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in basedir.glob("**/*.md") if not p.name.startswith(".")]
