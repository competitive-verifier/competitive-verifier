# The file is inspired by Tyrrrz/GitHubActionsTestLogger
# https://github.com/Tyrrrz/GitHubActionsTestLogger/blob/04fe7796a047dbd0e3cd6a46339b2a50f5125317/GitHubActionsTestLogger/TestSummary.cs

import os
import pathlib
from collections import Counter
from itertools import chain
from typing import TextIO

from competitive_verifier.models import FileResult, ResultStatus, VerifyCommandResult

SUCCESS = ResultStatus.SUCCESS
FAILURE = ResultStatus.FAILURE
SKIPPED = ResultStatus.SKIPPED


def to_human_str(total_seconds: float) -> str:
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
        return f"{int(total_seconds*1000)}ms"


def write_summary(fp: TextIO, result: VerifyCommandResult):
    def with_icon(icon: str, text: str) -> str:
        return icon + "&nbsp;&nbsp;" + text

    def write_table_line(cells: list[str]) -> None:
        for c in cells:
            fp.write("|")
            fp.write(c)
        fp.write("|\n")

    def write_table_file_result(results: list[tuple[pathlib.Path, FileResult]]) -> None:
        for p, fr in results:
            counter = Counter(r.status for r in fr.verifications)
            if counter.get(FAILURE):
                emoji_status = "❌"
            elif counter.get(SKIPPED):
                emoji_status = "⚠"
            else:
                emoji_status = "✔"
            write_table_line(
                [
                    with_icon(emoji_status, p.as_posix()),
                    str(counter.get(SUCCESS, "-")),
                    str(counter.get(FAILURE, "-")),
                    str(counter.get(SKIPPED, "-")),
                    str(sum(counter.values())),
                    to_human_str(sum(r.elapsed for r in fr.verifications)),
                ]
            )

    file_results: dict[bool, list[tuple[pathlib.Path, FileResult]]] = {
        False: [],
        True: [],
    }
    for p, fr in result.files.items():
        file_results[fr.newest].append((p, fr))

    file_results[True].sort(key=lambda t: t[0])
    file_results[False].sort(key=lambda t: t[0])
    counter = Counter(
        r.status
        for r in chain.from_iterable(f[1].verifications for f in file_results[True])
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
        with_icon("✓", "Passed"),
        with_icon("✘", "Failed"),
        with_icon("↷", "Skipped"),
        with_icon("∑", "Total"),
        with_icon("⧗", "Elapsed"),
    ]
    alignment = [":---"] + [":---:"] * (len(header) - 1)

    if file_results[True]:

        fp.write("## Results\n")
        write_table_line(header)
        write_table_line(alignment)
        write_table_line(
            [
                "_**Sum**_",
                str(counter.get(SUCCESS, "-")),
                str(counter.get(FAILURE, "-")),
                str(counter.get(SKIPPED, "-")),
                str(sum(counter.values())),
                to_human_str(result.total_seconds),
            ]
        )
        write_table_line([""] * len(header))

        write_table_file_result(file_results[True])

    if file_results[False]:
        fp.write("## Past results\n")
        write_table_line(header)
        write_table_line(alignment)
        write_table_file_result(file_results[False])
