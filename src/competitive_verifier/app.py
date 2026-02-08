import importlib.metadata
from argparse import ArgumentParser as BaseParser
from logging import getLogger
from typing import Annotated, Any, Literal, get_args

from pydantic import Field, TypeAdapter

from competitive_verifier.arg import BaseArguments
from competitive_verifier.documents import Docs
from competitive_verifier.download import Download
from competitive_verifier.inout import Check, MergeInput, MergeResult
from competitive_verifier.migrate import Migration
from competitive_verifier.oj import OjResolve
from competitive_verifier.verify import Verify

logger = getLogger(__name__)


class HelpError(Exception):
    pass


class NoSubcommand(BaseArguments):
    subcommand: Literal[None] = None  # noqa: PYI061

    def run(self) -> bool:
        raise HelpError

    @classmethod
    def add_parser(cls, parser: BaseParser):
        super().add_parser(parser)
        parser.add_argument(
            "--version",
            action="version",
            version=importlib.metadata.version("competitive-verifier"),
            help="print the competitive-verifier version number",
        )


Arguments = Annotated[
    NoSubcommand
    | Verify
    | Docs
    | Download
    | MergeInput
    | MergeResult
    | Check
    | OjResolve
    | Migration,
    Field(discriminator="subcommand"),
]
ARG_TYPES: tuple[type[BaseArguments], ...] = get_args(Arguments.__origin__)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]


class ArgumentParser(BaseParser):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        super().__init__(**kwargs)  # pyright: ignore[reportArgumentType]
        subparsers = self.add_subparsers(dest="subcommand", parser_class=BaseParser)

        for s in ARG_TYPES:
            s.add_parser(
                self
                if (sub := s.get_subcommand_info()) is None
                else subparsers.add_parser(**sub)
            )

    def parse(self, args: list[str] | None = None) -> Arguments:
        type_adapter = TypeAdapter[Arguments](Arguments)
        return type_adapter.validate_python(self.parse_args(args).__dict__)


def main(args: list[str] | None = None) -> int | None:
    parser = ArgumentParser()

    try:
        return not parser.parse(args).run()
    except HelpError:
        parser.print_help()
        return 2
