# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
import sys

import python.lib_all_success
from python.lib_some_skip_some_wa import stderr

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    stderr()
    print(python.lib_all_success.aplusb(a, b))


if __name__ == "__main__":
    main()
