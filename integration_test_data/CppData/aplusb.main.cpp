#define STANDALONE
#include <iostream>
#include <cassert>
#include <random>
#include "aplusb.hpp"
using namespace std;

int main()
{
    mt19937 rnd(random_device{}());
    for (size_t i = 0; i < 100000; i++)
    {
        auto a = rnd() % 1000000007;
        auto b = rnd() % 1000000007;
        // cout << (a + b) << " " << aplusb(a, b) << endl;
        assert((a + b) == aplusb(a, b));
    }
}
