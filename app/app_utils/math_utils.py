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
    """
    s = prompt.lower().replace(",", "")
    replacements = {
        "multiplied by": "*", "times": "*", "divided by": "/",
        "plus": "+", "minus": "-", "pi": "3.141592653589793"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)

    for pattern in [r"square root of\s*([0-9.]+)", r"square root\s*([0-9.]+)", r"sqrt\s*([0-9.]+)"]:
        s = re.sub(pattern, r"(\1**0.5)", s)
    s = re.sub(r"[a-z]", "", s)

    candidates = [c.strip() for c in re.findall(r"[0-9.+\-*/()\s]+", s) if re.search(r"\d", c)]
    if not candidates:
        return "Could not parse math expression."
    best_candidate = max(candidates, key=len, default="")

    if not best_candidate or not re.match(r"^[0-9.+\-*/()\s]+$", best_candidate):
        return "Error: unsafe characters in math expression." if best_candidate else "Could not parse math expression."

    try:
        res = eval(best_candidate, {"__builtins__": None}, {})
        if isinstance(res, (int, float)):
            if isinstance(res, float) and res.is_integer():
                return str(int(res))
            return f"{res:.10f}".rstrip("0").rstrip(".")
        return str(res)
    except ZeroDivisionError as e:
        return f"Error evaluating math expression: {e}"
    except Exception:
        return "Could not parse math expression."


if __name__ == "__main__":
    number: int = 84
    print(f"Prime factors of {number}: {get_prime_factors(number)}")
