import argparse
import os
import pathlib
import sys
from logging import getLogger
from typing import Optional

import competitive_verifier

_config_directory_name = competitive_verifier.config_dir.name


def find_project_root_directory() -> Optional[pathlib.Path]:
    dir = pathlib.Path.cwd()
    if (dir / _config_directory_name).exists():
        return dir
    for dir in dir.parents:
        if (dir / _config_directory_name).exists():
            return dir
    return None


# Move to directory which contains .competitive-verifier/
orig_directory = pathlib.Path.cwd()
root = find_project_root_directory()
if root is None:
    root = orig_directory
else:
    os.chdir(root)


logger = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.verify.main as verify

    default_verify_files_json = pathlib.Path(
        f"{_config_directory_name}/verify_files.json"
    )

    default_verify_result_json = pathlib.Path(
        f"{_config_directory_name}/verify_result.json"
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subcommand")

    subparser = subparsers.add_parser("verify")
    verify.argument_verify(subparser, default_json=default_verify_files_json)

    subparser = subparsers.add_parser("docs")
    docs.argument_docs(subparser, default_json=default_verify_result_json)

    subparser = subparsers.add_parser("download")
    download.argument_download(subparser, default_json=default_verify_result_json)

    return parser


def main(args: Optional[list[str]] = None):
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.verify.main as verify
    from competitive_verifier.log import configure_logging

    configure_logging()

    logger.info("Project root: %s", str(pathlib.Path.cwd().resolve(strict=True)))
    parser = get_parser()
    parsed = parser.parse_args(args)

    os.chdir(orig_directory)
    args_dict = vars(parsed)
    for k, v in args_dict.items():
        if isinstance(v, pathlib.Path):
            args_dict[k] = v.resolve(strict=True)
    os.chdir(root)

    if parsed.subcommand == "download":
        download.run(parsed)
    elif parsed.subcommand == "verify":
        verifier = verify.run(parsed)
        if not verifier.is_success():
            sys.exit(1)
    elif parsed.subcommand == "docs":
        docs.run(parsed)


if __name__ == "__main__":
    main()
