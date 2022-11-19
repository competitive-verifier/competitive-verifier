#define PROBLEM "https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/all/DSL_1_A"
#include <iostream>
#include "examples/cpp/cpp/union_find.hpp"
#include "examples/cpp/cpp/union_find.hpp"
#include "examples/cpp/cpp/union_find.hpp"
#include "examples/cpp/cpp/union_find.hpp"
#include "examples/cpp/cpp/union_find.hpp"
#include "examples/cpp/cpp/macros.hpp"
using namespace std;

int main() {
    int n, q; cin >> n >> q;
    union_find uft(n);
    REP (i, q) {
        int com, x, y; cin >> com >> x >> y;
        if (com == 0) {
            uft.unite_trees(x, y);
        } else if (com == 1) {
            cout << uft.is_same(x, y) << endl;
        }
    }
    return 0;
}
