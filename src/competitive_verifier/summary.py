# The file is inspired by Tyrrrz/GitHubActionsTestLogger
# https://github.com/Tyrrrz/GitHubActionsTestLogger/blob/04fe7796a047dbd0e3cd6a46339b2a50f5125317/GitHubActionsTestLogger/TestSummary.cs

import os
import pathlib
from collections import Counter
from itertools import chain
from typing import Optional, TextIO

from competitive_verifier.models import (
    FileResult,
    JudgeStatus,
    ResultStatus,
    TestcaseResult,
    VerifyCommandResult,
)

SUCCESS = ResultStatus.SUCCESS
FAILURE = ResultStatus.FAILURE
SKIPPED = ResultStatus.SKIPPED


def to_human_str_seconds(total_seconds: float) -> str:
    hours = int(total_seconds // 3600)
    rm = total_seconds % 3600
    minutes = int(rm // 60)
    rm %= 60
    seconds = rm

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {int(seconds)}s"
    elif total_seconds >= 10:
        return f"{int(seconds)}s"
    elif total_seconds > 1:
        return f"{total_seconds:.1f}s"
    else:
        return f"{int(total_seconds * 1000)}ms"


def to_human_str_mega_bytes(total_mega_bytes: float) -> str:
    if total_mega_bytes < 0.001:
        return "0MB"
    if total_mega_bytes < 100:
        return f"{total_mega_bytes:.3g}MB"
    return f"{int(total_mega_bytes)}MB"


class TableWriter:
    def __init__(self, fp: TextIO, header: list[str]) -> None:
        self.size = len(header)
        self.fp = fp
        self.write_table_line(*header)

    def write_table_line(self, *cells: str) -> None:
        assert len(cells) == self.size
        fp = self.fp
        for c in cells:
            fp.write("|")
            fp.write(c)
        fp.write("|\n")


def write_summary(fp: TextIO, result: VerifyCommandResult):
    def with_icon(icon: str, text: str) -> str:
        return icon + "&nbsp;&nbsp;" + text

    file_results: list[tuple[pathlib.Path, FileResult]] = []
    past_results: list[tuple[pathlib.Path, FileResult]] = []
    for p, fr in result.files.items():
        if fr.newest:
            file_results.append((p, fr))
        else:
            past_results.append((p, fr))

    file_results.sort(key=lambda t: t[0])
    past_results.sort(key=lambda t: t[0])
    counter = Counter(
        r.status for r in chain.from_iterable(f[1].verifications for f in file_results)
    )

    fp.write("# ")

    if counter.get(FAILURE):
        emoji_status = "❌"
    elif counter.get(SKIPPED):
        emoji_status = "⚠"
    else:
        emoji_status = "✔"

    fp.write(emoji_status)
    fp.write(" ")
    fp.write(os.getenv("COMPETITIVE_VERIFY_SUMMARY_TITLE", "Verification result"))
    fp.write("\n\n")

    fp.write("- ")
    fp.write(with_icon("✔", "All test case results are `success`"))
    fp.write("\n")
    fp.write("- ")
    fp.write(with_icon("❌", "Test case results containts `failure`"))
    fp.write("\n")
    fp.write("- ")
    fp.write(with_icon("⚠", "Test case results containts `skipped`"))
    fp.write("\n\n\n")

    header = [
        with_icon("📝", "File"),
        "✔<br>Passed",
        "❌<br>Failed",
        "⚠<br>Skipped",
        "∑<br>Total",
        "⏳<br>Elapsed",
        "🦥<br>Slowest",
        "🐘<br>Heaviest",
    ]
    alignment = [":---"] + [":---:"] * (len(header) - 1)

    def write_table_file_result(results: list[tuple[pathlib.Path, FileResult]]) -> None:
        for p, fr in results:
            counter = Counter(r.status for r in fr.verifications)
            if counter.get(FAILURE):
                emoji_status = "❌"
            elif counter.get(SKIPPED):
                emoji_status = "⚠"
            else:
                emoji_status = "✔"
            elapsed = sum(r.elapsed for r in fr.verifications)
            slowest = max(
                (r.slowest for r in fr.verifications if r.slowest is not None),
                default=None,
            )
            heaviest = max(
                (r.heaviest for r in fr.verifications if r.heaviest is not None),
                default=None,
            )
            tb.write_table_line(
                with_icon(emoji_status, p.as_posix()),
                str(counter.get(SUCCESS, "-")),
                str(counter.get(FAILURE, "-")),
                str(counter.get(SKIPPED, "-")),
                str(sum(counter.values())),
                to_human_str_seconds(elapsed),
                "-" if slowest is None else to_human_str_seconds(slowest),
                "-" if heaviest is None else to_human_str_mega_bytes(heaviest),
            )

    if file_results:
        fp.write("## Results\n")
        tb = TableWriter(fp, header)
        tb.write_table_line(*alignment)
        tb.write_table_line(
            "_**Sum**_",
            str(counter.get(SUCCESS, "-")),
            str(counter.get(FAILURE, "-")),
            str(counter.get(SKIPPED, "-")),
            str(sum(counter.values())),
            to_human_str_seconds(result.total_seconds),
            "-",
            "-",
        )
        tb.write_table_line(*[""] * len(header))

        write_table_file_result(file_results)

    if past_results:
        fp.write("## Past results\n")
        tb = TableWriter(fp, header)
        tb.write_table_line(*alignment)
        write_table_file_result(past_results)

    if counter.get(FAILURE):
        assert file_results
        first_failure = True
        for p, fr in file_results:
            cases = [
                DisplayTestcaseResult(
                    environment=v.verification_name, **(c.model_dump())
                )
                for v in fr.verifications
                for c in (v.testcases or [])
                if c.status != JudgeStatus.AC
            ]
            if not cases:
                continue
            if first_failure:
                fp.write("## Failed tests\n\n")
                first_failure = False
            fp.write(f"### {p.as_posix()}\n\n")

            etb = TableWriter(fp, ["env", "name", "status", "Elapsed", "Memory"])
            etb.write_table_line(*[":---"] * 2 + [":---:"] * 3)

            for c in cases:
                etb.write_table_line(
                    c.environment or "",
                    c.name,
                    c.status.name,
                    c.elapsed_str,
                    c.memory_str,
                )


class DisplayTestcaseResult(TestcaseResult):
    environment: Optional[str]

    @property
    def elapsed_str(self):
        return to_human_str_seconds(self.elapsed)

    @property
    def memory_str(self):
        return to_human_str_mega_bytes(self.memory) if self.memory else "-"
