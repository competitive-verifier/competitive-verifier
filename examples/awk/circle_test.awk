# competitive-verifier: PROBLEM https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_4_B
# competitive-verifier: ERROR 1e-5
@include "examples/awk/circle.awk"
{
    print get_area($1), get_circumference($1);
}
