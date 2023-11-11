import importlib.resources
import pathlib
import shutil
from logging import getLogger
from typing import Optional

from pydantic import BaseModel

import competitive_verifier.git as git
import competitive_verifier.github as github
from competitive_verifier.models import VerificationInput, VerifyCommandResult

from .config import ConfigYaml, load_config_yml
from .front_matter import Markdown
from .render import RenderJob
from .static_files import default_resource_files

logger = getLogger(__name__)


_RESOURCE_PACKAGE = "competitive_verifier_resources"
_DOC_USAGE_PATH = "doc_usage.txt"


class DocumentBuilder(BaseModel):
    input: VerificationInput
    result: VerifyCommandResult
    docs_dir: pathlib.Path
    destination_dir: pathlib.Path
    include: Optional[list[str]]
    exclude: Optional[list[str]]

    def build(self) -> bool:
        logger.info(
            "Working directory: %s",
            pathlib.Path.cwd().as_posix(),
        )

        logger.info("Generate documents...")

        # implementation
        result = self.impl()

        logger.info("Generated.")
        logger.info(
            (importlib.resources.files(_RESOURCE_PACKAGE) / _DOC_USAGE_PATH)
            .read_text(encoding="utf-8")
            .replace("{{{{{markdown_dir_path}}}}}", self.destination_dir.as_posix())
            .replace(
                "{{{{{repository}}}}}",
                github.env.get_repository()
                or "competitive-verifier/competitive-verifier",
            )
        )

        return result

    def impl(self) -> bool:
        self.destination_dir.mkdir(parents=True, exist_ok=True)

        config_yml = load_config_yml(self.docs_dir)
        logger.info("_config.yml: %s", config_yml)

        index_md_path = self.docs_dir / "index.md"
        if index_md_path.exists():
            index_md = Markdown.load_file(index_md_path)
        else:
            index_md = None

        # Write code documents.
        self.write_code_docs(
            config_yml=config_yml,
            index_md=index_md,
            static_dir=self.docs_dir / "static",
        )

        # Write _config.yml
        (self.destination_dir / "_config.yml").write_bytes(config_yml.model_dump_yml())

        # Copy static files
        self.copy_static_files(static_dir=self.docs_dir / "static")
        return True

    def copy_static_files(self, *, static_dir: pathlib.Path):
        logger.info("Copy library static files...")
        for path, content in default_resource_files():
            file_dst = self.destination_dir / path
            logger.debug("Writing to %s", file_dst.as_posix())
            if not file_dst.exists():
                file_dst.parent.mkdir(parents=True, exist_ok=True)
            file_dst.write_bytes(content)

        logger.info("Copy user static files...")
        try:
            if static_dir.is_dir():
                shutil.copytree(
                    static_dir,
                    self.destination_dir,
                    dirs_exist_ok=True,
                )
        except Exception as e:
            logger.exception("Failed to copy user static files.", e)

    def write_code_docs(
        self,
        *,
        config_yml: ConfigYaml,
        index_md: Optional[Markdown],
        static_dir: Optional[pathlib.Path],
    ):
        logger.info("Write document files...")

        exclude = (self.exclude or []) + (config_yml.exclude or [])
        if static_dir and static_dir.is_relative_to("."):
            exclude.append(self.docs_dir.relative_to(".").as_posix())

        sources = git.ls_files(*(self.include or []))
        if exclude:
            sources -= git.ls_files(*exclude)

        # yield source.with_suffix(source.suffix + ".md"), source.read_bytes()
        for job in RenderJob.enumerate_jobs(
            sources=sources,
            input=self.input,
            result=self.result,
            config=config_yml,
            index_md=index_md,
        ):
            logger.debug(job)
            dst = self.destination_dir / job.destination_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            logger.info("writing to %s", dst.as_posix())
            with dst.open("wb") as fp:
                job.write_to(fp)
