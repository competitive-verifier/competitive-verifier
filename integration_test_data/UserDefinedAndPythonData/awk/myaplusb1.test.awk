# competitive-verifier: LOCALCASE ./myaplusb
@include "awk/aplusb.awk"
{
    print add($1,$2);
}
