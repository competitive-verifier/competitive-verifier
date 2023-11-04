import argparse
import pathlib
from pytest_mock import MockerFixture

import competitive_verifier.oj as oj


def test_oj_test(mocker: MockerFixture):
    run = mocker.patch("competitive_verifier.oj.run_test")

    oj.test(url="http://example.com", command="ls .", tle=2, error=None, mle=128)

    run.assert_called_once()
    args = run.call_args[0][0]

    assert isinstance(args, argparse.Namespace)
    assert args.subcommand == "test"
    assert args.print_input is True
    assert args.cookie == pathlib.Path("/bar/baz/online-judge-tools") / "cookie.txt"
    assert args.tle == 2.0
    assert args.mle == 128.0
    assert args.error is None
    assert args.command == "ls ."
    assert args.directory == pathlib.Path(
        ".competitive-verifier/cache/problems/a9b9f04336ce0181a08e774e01113b31/test"
    )
