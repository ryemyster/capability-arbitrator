"""
File: primes.py
Purpose: Provides utility functions for prime factorization.
Why it exists: To provide a centralized, reliable method for decomposing integers into their prime constituents.
How it works: Implements a trial division algorithm to efficiently identify prime factors.
"""

from typing import List


def get_prime_factors(n: int) -> List[int]:
    """
    Compute the prime factors of a given integer n.

    Args:
        n: The integer to factorize. Must be greater than 1.

    Returns:
        A list of prime factors in ascending order.
    """
    if n < 2:
        return []

    factors: List[int] = []
    divisor: int = 2

    temp: int = n
    while divisor * divisor <= temp:
        while temp % divisor == 0:
            factors.append(divisor)
            temp //= divisor
        divisor += 1

    if temp > 1:
        factors.append(temp)

    return factors
