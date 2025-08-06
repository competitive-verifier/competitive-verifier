// competitive-verifier: STANDALONE
#include <iostream>
#include <cassert>
#include <random>
#include "examples/cpp/bit_minus.hpp"
using namespace std;

int main()
{
    mt19937 rnd(random_device{}());
    for (size_t i = 0; i < 100000; i++)
    {
        auto num = rnd();
        // cout << num << " " << bit_minus(num) << endl;
        assert(-(int64_t)num == bit_minus(num));
    }
    return 0;
}
