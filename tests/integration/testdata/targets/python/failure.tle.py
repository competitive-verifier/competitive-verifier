# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
# competitive-verifier: TLE 0.09
import sys
import time

import testdata.targets.python.lib_all_failure

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    if a % 2 == 0:
        time.sleep(0.1)
    print(testdata.targets.python.lib_all_failure.aplusb(a, b))


if __name__ == "__main__":
    main()
