import pathlib
import re
import shutil
import urllib.parse
from logging import getLogger
from typing import Optional

import yaml

import competitive_verifier.git as git
from competitive_verifier.documents.render import resolve_documentation_of
from competitive_verifier.exec import exec_command
from competitive_verifier.oj.verify.languages.cplusplus import CPlusPlusLanguage
from competitive_verifier.oj.verify.languages.go import GoLanguage
from competitive_verifier.oj.verify.languages.haskell import HaskellLanguage
from competitive_verifier.oj.verify.languages.java import JavaLanguage
from competitive_verifier.oj.verify.languages.nim import NimLanguage
from competitive_verifier.oj.verify.languages.python import PythonLanguage
from competitive_verifier.oj.verify.languages.ruby import RubyLanguage
from competitive_verifier.oj.verify.languages.rust import RustLanguage
from competitive_verifier.oj.verify.list import OjVerifyConfig
from competitive_verifier.oj.verify.models import Language

logger = getLogger(__name__)


_title_pattern = re.compile(r"@(?:title|brief) (.*)")
_docs_pattern = re.compile(r"@docs (.*)$", re.MULTILINE)
_documentation_of_pattern = re.compile(r"^documentation_of:.*", re.MULTILINE)

_problem_pattern = re.compile(r"#define PROBLEM(?:\\\n| |\t)+(.+)")
_error_pattern = re.compile(r"#define ERROR(?:\\\n| |\t)+(.+)")


def problem_subn(content: str) -> tuple[str, int]:
    return _problem_pattern.subn(
        lambda m: f"// competitive-verifier: PROBLEM {_strip_quote(m.group(1))}",
        content,
    )


def error_subn(content: str) -> tuple[str, int]:
    return _error_pattern.subn(
        lambda m: f"// competitive-verifier: ERROR {_strip_quote(m.group(1))}", content
    )


_yukicoder_pattern = re.compile(r"[^#]*YUKICODER_TOKEN: .*")


def migrate_conf_dir(*, dry_run: bool):
    old_conf_dir = pathlib.Path(".verify-helper")
    new_conf_dir = pathlib.Path(".competitive-verifier")
    old_docs_dir = old_conf_dir / "docs"
    new_docs_dir = new_conf_dir / "docs"
    if not old_docs_dir.exists():
        return

    if not new_docs_dir.exists():
        gitignore = new_conf_dir / ".gitignore"
        if not dry_run:
            new_docs_dir.mkdir(parents=True, exist_ok=True)
            gitignore.write_bytes(b"/*/\n!docs/")
        logger.warning("Create directory: %s", new_docs_dir.as_posix())

    for p in old_docs_dir.glob("**/*"):
        relative = p.relative_to(old_docs_dir)
        new_path = new_docs_dir / relative
        if p.is_dir():
            logger.warning("Create directory: %s", new_path.as_posix())
            new_path.mkdir(parents=True, exist_ok=True)
        elif p.is_file():
            logger.warning("Move docs file: %s → %s", p.as_posix(), new_path.as_posix())
            if not dry_run:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, new_path)
                p.unlink(missing_ok=True)
    shutil.rmtree(old_docs_dir)


def _get_docs_path(content: str, *, path: pathlib.Path) -> Optional[pathlib.Path]:
    docs_match = _docs_pattern.search(content)
    if docs_match:
        doc_path = docs_match.group(1)
        if isinstance(doc_path, str):
            return resolve_documentation_of(
                doc_path.strip(),
                basedir=path.parent,
            )
    return None


def _strip_quote(s: str) -> str:
    return s.strip().strip("\"'")


def migrate_cpp_annotations(path: pathlib.Path, *, dry_run: bool):
    hit = False
    logger.debug("Migrate file: %s", path.as_posix())
    content = path.read_text(encoding="utf-8")

    new_content, hit_cnt = problem_subn(content)
    if hit_cnt > 0:
        logger.warning(
            "[Updated] %s: Replace `#define PROBLEM` to `competitive-verifier: PROBLEM`",
            path.as_posix(),
        )
        content = new_content
        hit = True

    new_content, hit_cnt = error_subn(content)
    if hit_cnt > 0:
        logger.warning(
            "[Updated] %s: Replace `#define ERROR` to `competitive-verifier: ERROR`",
            path.as_posix(),
        )
        content = new_content
        hit = True

    doc_path = _get_docs_path(content, path=path)
    if doc_path:
        if not doc_path.exists():
            logger.error("`%s` doesn't exits.", doc_path.as_posix())

        docs = doc_path.read_text("utf-8")
        docs_lines = docs.splitlines(keepends=True)

        logger.warning("[Updated] %s: Remove `@docs`", path.as_posix())
        content, _ = _docs_pattern.subn("", content)
        hit = True

        if _documentation_of_pattern.search(docs):
            logger.debug(
                "[Not Updated] %s: Add `documentation_of:`",
                doc_path.as_posix(),
            )
        else:
            logger.warning(
                "[Updated] %s: Add `documentation_of:`",
                doc_path.as_posix(),
            )
            documentation_of = f"documentation_of: //{path.as_posix()}\n"
            if docs.startswith("---"):
                docs_lines.insert(1, documentation_of)
            else:
                docs_lines[0:0] = [
                    "---\n",
                    documentation_of,
                    "---\n\n",
                ]
            if not dry_run:
                doc_path.write_text("".join(docs_lines), encoding="utf-8")

    if hit:
        if not dry_run:
            path.write_text(content, "utf-8")
    else:
        logger.debug("Not updated: %s", path.as_posix())


def _lang_type_to_str(lang: Optional[Language]) -> Optional[str]:
    if isinstance(lang, CPlusPlusLanguage):
        return "cpp"
    if isinstance(lang, GoLanguage):
        return "go"
    if isinstance(lang, HaskellLanguage):
        return "haskel"
    if isinstance(lang, JavaLanguage):
        return "java"
    if isinstance(lang, NimLanguage):
        return "nim"
    if isinstance(lang, PythonLanguage):
        return "python"
    if isinstance(lang, RubyLanguage):
        return "ruby"
    if isinstance(lang, RustLanguage):
        return "rust"
    return None


def _get_action_query(languages: set[str]) -> dict[str, str]:
    d = {
        "configToml": ".verify-helper/config.toml",
        "langs": "|".join(languages),
    }
    if not pathlib.Path(d["configToml"]).exists():
        del d["configToml"]
    remote = exec_command(
        ["git", "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    if remote:
        d["repository"] = remote

    workflow_path = pathlib.Path(".github/workflows/verify.yml")
    if workflow_path.exists():
        workflow = workflow_path.read_text()
        if _yukicoder_pattern.search(workflow):
            d["tokens"] = "yuki"

    jekyll_config_path = pathlib.Path(".competitive-verifier/docs/_config.yml")
    if jekyll_config_path.exists():
        with jekyll_config_path.open("r") as fp:
            jekyll_config = yaml.safe_load(fp)
        try:
            exclude = jekyll_config.get("exclude")
            if isinstance(exclude, list):
                exclude = "\n".join(
                    exclude  # pyright: ignore[reportUnknownArgumentType]
                )
            if exclude:
                d["exclude"] = exclude
        except Exception:
            pass
    return d


def main(dry_run: bool) -> bool:
    migrate_conf_dir(dry_run=dry_run)

    languages = set[str]()
    lang_dict = OjVerifyConfig().get_dict()

    for path in git.ls_files():
        lang = lang_dict.get(path.suffix)
        if isinstance(lang, CPlusPlusLanguage):
            migrate_cpp_annotations(path, dry_run=dry_run)
        lang_str = _lang_type_to_str(lang)
        if lang_str:
            languages.add(lang_str)

    d = _get_action_query(languages)

    logger.info("Complete migrations")
    print("Next steps")
    # page = "http://localhost:4000"
    page = "https://competitive-verifier.github.io/competitive-verifier"
    print(f"  1. Open {page}/installer.html?{urllib.parse.urlencode(d)}")
    print("  2. Update your GitHub Actions.")
    return True
