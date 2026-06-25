import unittest
from app.app_utils.math_utils import get_prime_factors, solve_math
from app.app_utils.telemetry import calculate_savings

class TestPrimeFactors(unittest.TestCase):
    def test_get_prime_factors(self):
        self.assertEqual(get_prime_factors(1), [])
        self.assertEqual(get_prime_factors(2), [2])
        self.assertEqual(get_prime_factors(3), [3])
        self.assertEqual(get_prime_factors(4), [2, 2])
        self.assertEqual(get_prime_factors(6), [2, 3])
        self.assertEqual(get_prime_factors(12), [2, 2, 3])
        self.assertEqual(get_prime_factors(25), [5, 5])
        self.assertEqual(get_prime_factors(31), [31])

    def test_solve_math_word_problem(self):
        self.assertEqual(solve_math("What is 2500 multiplied by 4?"), "10000")

    def test_math_telemetry_keeps_node_tokens_zero(self):
        run = calculate_savings({
            "prompt": "What is 2500 multiplied by 4?",
            "node_name": "math",
            "node_input_tokens": 0,
            "node_output_tokens": 0,
        })
        self.assertEqual(run["node_input_tokens"], 0)
        self.assertEqual(run["node_output_tokens"], 0)

if __name__ == '__main__':
    unittest.main()
