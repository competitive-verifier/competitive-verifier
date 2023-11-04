# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
# competitive-verifier: MLE 10
import sys

import targets.python.lib_all_failure
from targets.python.lib_some_failure import MB

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    if a % 2 == 0:
        sum([1] * 10 * MB)
    print(targets.python.lib_all_failure.aplusb(a, b))


if __name__ == "__main__":
    main()
