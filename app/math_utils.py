"""
Purpose: Provide mathematical utility functions.
Why: Centralizes common math operations for consistency.
How: Import the desired function from this module.
"""

def get_prime_factors(n: int) -> list[int]:
    """Computes the prime factors of a given integer n.

    Args:
        n (int): The integer to factorize.

    Returns:
        list[int]: A list of prime factors.
    """
    factors: list[int] = []
    d: int = 2
    temp: int = n
    while d * d <= temp:
        while temp % d == 0:
            factors.append(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.append(temp)
    return factors
