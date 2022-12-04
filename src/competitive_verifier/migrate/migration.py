import pathlib
import re
import shutil
from logging import getLogger
from typing import Optional

import competitive_verifier.git as git
from competitive_verifier.documents.job import resolve_documentation_of
from competitive_verifier_oj_clone.languages.cplusplus import CPlusPlusLanguage
from competitive_verifier_oj_clone.list import get as get_lang

logger = getLogger(__name__)


def migrate_conf_dir(*, dry_run: bool):
    old_conf_dir = pathlib.Path(".verify-helper")
    new_conf_dir = pathlib.Path(".competitive-verifier")
    if not old_conf_dir.exists():
        return

    if not new_conf_dir.exists():
        if not dry_run:
            new_conf_dir.mkdir(parents=True, exist_ok=True)
        logger.warning("Create directory: %s", new_conf_dir.as_posix())

    for p in old_conf_dir.glob("**/*"):
        relative = p.relative_to(old_conf_dir)
        new_path = new_conf_dir / relative
        if p.is_dir():
            logger.warning("Create directory: %s", new_path.as_posix())
            new_path.mkdir(parents=True, exist_ok=True)
        elif p.is_file():
            logger.warning("Move docs file: %s → %s", p.as_posix(), new_path.as_posix())
            if not dry_run:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, new_path)
                p.unlink(missing_ok=True)
    shutil.rmtree(old_conf_dir)


_title_pattern = re.compile(r".*@(?:title|brief) (.*)")
_docs_pattern = re.compile(r"@docs (.*)$", re.MULTILINE)
_documentation_of_pattern = re.compile(r"^documentation_of:.*", re.MULTILINE)

_problem_pattern = re.compile(
    r'#define PROBLEM "(.+)"',
    re.MULTILINE,
)
_error_pattern = re.compile(r"#define ERROR (.*)", re.MULTILINE)


def _get_docs_path(content: str, *, path: pathlib.Path) -> Optional[pathlib.Path]:
    docs_match = _docs_pattern.search(content)
    if docs_match:
        doc_path = docs_match.group(1)
        if isinstance(doc_path, str):
            return resolve_documentation_of(doc_path.strip(), basepath=path)
    return None


def migrate_cpp_annotations(path: pathlib.Path, *, dry_run: bool):
    if not isinstance(get_lang(path), CPlusPlusLanguage):
        return
    hit = False
    logger.debug("Migrate file: %s", path.as_posix())
    content = path.read_text(encoding="utf-8")

    if "competitive-verifier: document_title" not in content:
        new_content, hit_cnt = _title_pattern.subn(
            r"// competitive-verifier: document_title \1", content, 1
        )

        if hit_cnt > 0:
            logger.warning(
                "[Updated] %s: Add `competitive-verifier: document_title`",
                path.as_posix(),
            )
            content = new_content
            hit = True

    new_content, hit_cnt = _problem_pattern.subn(
        r"// competitive-verifier: PROBLEM \1", content
    )
    if hit_cnt > 0:
        logger.warning(
            "[Updated] %s: Replace `#define PROBLEM` to `competitive-verifier: PROBLEM`",
            path.as_posix(),
        )
        content = new_content
        hit = True

    new_content, hit_cnt = _problem_pattern.subn(
        r"// competitive-verifier: ERROR \1", content
    )
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
                doc_path.write_text("".join(docs_lines))

    if hit:
        if not dry_run:
            path.write_text(content, "utf-8")
    else:
        logger.debug("Not updated: %s", path.as_posix())


def main(dry_run: bool) -> bool:
    migrate_conf_dir(dry_run=dry_run)
    for file in git.ls_files():
        migrate_cpp_annotations(file, dry_run=dry_run)

    return True
