# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
# competitive-verifier: IGNORE
import sys

import targets.python.lib_skip
from targets.python.lib_some_skip_some_wa import stderr

input = sys.stdin.buffer.readline


def main() -> None:
    stderr()
    a, b = map(int, input().split())
    print(targets.python.lib_skip.aplusb(a, b))


if __name__ == "__main__":
    main()
