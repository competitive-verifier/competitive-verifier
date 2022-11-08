# The file is inspired by Tyrrrz/GitHubActionsTestLogger
# https://github.com/Tyrrrz/GitHubActionsTestLogger/blob/04fe7796a047dbd0e3cd6a46339b2a50f5125317/GitHubActionsTestLogger/TestSummary.cs

import os
from collections import Counter
from itertools import chain
from typing import TextIO

from competitive_verifier.models import VerifyCommandResult
from competitive_verifier.models.result import ResultStatus


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
    counter = Counter(
        r.status
        for r in chain.from_iterable(f.command_results for f in result.files.values())
    )

    def counter_str(s: ResultStatus, default: str = "—") -> str:
        v = counter.get(s, 0)
        if v > 0:
            return str(v)
        return default

    fp.write("<details>")
    fp.write("<summary>")

    if counter.get(ResultStatus.FAILURE):
        circle_status = "🔴"
    elif counter.get(ResultStatus.SKIPPED):
        circle_status = "🟡"
    else:
        circle_status = "🟢"

    fp.write(circle_status)
    fp.write(" ")
    fp.write("<b>")
    fp.write(os.getenv("COMPETITIVE_VERIFY_SUMMARY_TITLE", "Verification result"))
    fp.write("</b>")
    fp.write("</summary>")
    fp.write("<br/>")

    def table_header(icon: str, text: str) -> None:
        fp.write('<th width="99999">')
        fp.write(icon)
        fp.write("&nbsp;&nbsp;")
        fp.write(text)
        fp.write("</th>")

    fp.write("<table>")
    table_header("✓", "Passed")
    table_header("✘", "Failed")
    table_header("↷", "Skipped")
    table_header("∑", "Total")
    table_header("⧗", "Elapsed")
    fp.write("<tr>")
    fp.write('<td align="center">')
    fp.write(counter_str(ResultStatus.SUCCESS, "-"))
    fp.write("</td>")
    fp.write('<td align="center">')
    fp.write(counter_str(ResultStatus.FAILURE, "-"))

    fp.write("</td>")
    fp.write('<td align="center">')
    fp.write(counter_str(ResultStatus.SKIPPED, "-"))
    fp.write("</td>")
    fp.write('<td align="center">')
    fp.write(str(sum(counter.values())))
    fp.write("</td>")
    fp.write('<td align="center">')
    fp.write(to_human_str(result.total_seconds))
    fp.write("</td>")
    fp.write("</tr>")
    fp.write("</table>")
    fp.write("\n\n")

    fp.write("</details>\n")
