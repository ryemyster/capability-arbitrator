import unittest
from app.app_utils.math_utils import get_prime_factors

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

if __name__ == '__main__':
    unittest.main()
