import onlinejudge.utils
from onlinejudge_command.main import get_parser
import onlinejudge_command.subcommand.download as oj_download
import competitive_verifier.util

onlinejudge.utils.user_cache_dir = competitive_verifier.util.cache_dir / "oj"


def download() -> None:
    parser = get_parser()
    args = parser.parse_args(["download"])
    oj_download.run(args)
