# verification-helper: PROBLEM https://judge.yosupo.jp/problem/unionfind
import sys
input = sys.stdin.buffer.readline

from examples.python.union_find import UnionFind


def main() -> None:
    N, Q = map(int, input().split())
    uf = UnionFind(N)
    for _ in range(Q):
        t, u, v = map(int, input().split())
        if t == 0:
            uf.unite(u, v)
        else:
            print(int(uf.is_same(u, v)))


if __name__ == "__main__":
    main()
