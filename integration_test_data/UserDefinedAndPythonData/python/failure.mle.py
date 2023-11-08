# competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
# competitive-verifier: MLE 100
import pathlib
import sys

import python.lib_all_failure
from python.lib_some_failure import MB

input = sys.stdin.buffer.readline


def main() -> None:
    a, b = map(int, input().split())
    if a % 2 == 0:
        dir = pathlib.Path(__file__).parent.parent.parent / "dst_dir"
        dir.mkdir(exist_ok=True, parents=True)
        file = dir / "buffer.txt"
        file.write_bytes(b"a" * 100 * MB)
        file.unlink(missing_ok=True)
    print(python.lib_all_failure.aplusb(a, b))


if __name__ == "__main__":
    main()
