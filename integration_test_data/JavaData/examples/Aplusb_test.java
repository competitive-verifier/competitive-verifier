// competitive-verifier: PROBLEM https://judge.yosupo.jp/problem/aplusb
package examples;
import java.util.Scanner;
import examples.Aplusb;

public class Aplusb_test {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(Aplusb.plus(a, b));
    }
}
