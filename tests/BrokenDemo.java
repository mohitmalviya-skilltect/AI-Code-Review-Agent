public class BrokenDemo {
    public static void main(String[] args) {
        // Syntax & Type Errors
        int number = "100";
        String greeting = "Hello World"
        
        // Logical & Runtime Errors
        int[] numbers = {1, 2, 3};
        System.out.println(numbers[5]);

        int result = 10 / 0;

        // Scope & Method Errors
        nonExistentMethod();
        System.out.println(secretKey);

        // Accessing null reference
        String text = nul;
        System.out.println(text.length());
    }
}