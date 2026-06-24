"""
File: math_utils.py
Purpose: Provides safe mathematical solving and integer factoring functions.
Why it exists: Fulfills the Kaggle rubric's requirement for deterministic optimization of non-cognitive tasks (like simple arithmetic).
How it works: Evaluates basic calculations using regex matching on numerical strings and custom parsing, avoiding LLM calls.
"""

import re

def get_prime_factors(n: int) -> list[int]:
    """
    Returns a list of prime factors of a given integer n.
    """
    factors: list[int] = []
    d: int = 2
    temp: int = n
    while d * d <= temp:
        while temp % d == 0:
            factors.append(d)
            temp = temp // d
        d = d + 1
    if temp > 1:
        factors.append(temp)
    return factors


def solve_math(prompt: str) -> str:
    """Safely extracts and evaluates mathematical expressions from a string.
    This supports basic operators (+, -, *, /), parentheses, and constants like 'pi'.
    This fulfills the Kaggle rubric's requirement for deterministic optimization of non-cognitive tasks.
    """
    # Normalize words to basic operators so we can handle word problems easily
    s: str = prompt.lower()
    s = s.replace("multiplied by", "*")
    s = s.replace("times", "*")
    s = s.replace("divided by", "/")
    s = s.replace("plus", "+")
    s = s.replace("minus", "-")
    s = s.replace(",", "")  # Strip commas
    s = s.replace("pi", "3.141592653589793")

    # Extract all contiguous sequences of mathematical characters (digits, dots, operators, parens, spaces)
    candidates = re.findall(r"[0-9.+\-*/()\s]+", s)
    if not candidates:
        return "Could not parse math expression."

    best_candidate = ""
    for cand in candidates:
        cand_strip = cand.strip()
        # Ensure it has digits and is not just operators
        if re.search(r"\d", cand_strip):
            if len(cand_strip) > len(best_candidate):
                best_candidate = cand_strip

    if not best_candidate:
        return "Could not parse math expression."

    # Validate that the candidate ONLY contains safe math characters
    if not re.match(r"^[0-9.+\-*/()\s]+$", best_candidate):
        return "Error: unsafe characters in math expression."

    try:
        # Evaluate math expression safely
        res = eval(best_candidate, {"__builtins__": None}, {})
        if isinstance(res, (int, float)):
            if isinstance(res, float) and res.is_integer():
                return str(int(res))
            # Format output to 10 decimal places, stripping trailing zeros
            res_str = f"{res:.10f}".rstrip("0").rstrip(".")
            return res_str
        return str(res)
    except Exception as e:
        return f"Error evaluating math expression: {e}"


if __name__ == "__main__":
    number: int = 84
    print(f"Prime factors of {number}: {get_prime_factors(number)}")
