// competitive-verifier: STANDALONE
package examples;
import java.util.Random;
import examples.Aplusb;

public class Aplusb_main {
    public static void main(String[] args) {
        Random rnd = new Random();
        for (int i = 0; i < 100000; i++)
        {
            int a = rnd.nextInt(1000000);
            int b = rnd.nextInt(1000000);

            if (Aplusb.plus(a, b) != a + b)
                throw new RuntimeException();
        }
    }
}
