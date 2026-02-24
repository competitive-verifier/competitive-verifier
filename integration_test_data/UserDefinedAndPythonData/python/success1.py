# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
import sys

import python.lib_some_skip
from python.lib_some_failure import KB

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    if KB < 1000:
        print("No")
    print(python.lib_some_skip.aplusb(a, b))


if __name__ == "__main__":
    main()


# 'https://example.com/top_single
# "https://example.com/top_double
# `https://example.com/top_back
# 'https://example.com/single'
# "https://example.com/double"
# `https://example.com/back`