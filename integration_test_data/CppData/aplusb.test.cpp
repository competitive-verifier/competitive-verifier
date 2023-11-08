#define PROBLEM "https://judge.yosupo.jp/problem/aplusb"
#include <iostream>
#include "macros.hpp"
#include "aplusb.hpp"
using namespace std;

int main()
{
    int a, b;
    cin >> a >> b;

    int c = aplusb(a, b);
    OUT(c);
    return 0;
}
