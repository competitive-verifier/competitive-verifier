# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
import sys

import targets.python.lib_all_failure

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    print(testdata.targets.python.lib_all_failure.aplusb(a // 0, b))


if __name__ == "__main__":
    main()
