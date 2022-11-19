#define PROBLEM "https://judge.yosupo.jp/problem/unionfind"
#include <iostream>
#include "examples/cpp/union_find.hpp"
#include "examples/cpp/macros.hpp"
using namespace std;

int main() {
    int n, q; cin >> n >> q;
    union_find uf(n);
    REP (i, q) {
        int t, u, v; cin >> t >> u >> v;
        if (t == 0) {
            uf.unite_trees(u, v);
        } else if (t == 1) {
            cout << uf.is_same(u, v) << endl;
        }
    }
    return 0;
}
