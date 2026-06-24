def reverse_string(s):
    return s[::-1]

if __name__ == "__main__":
    test_string = "hello"
    reversed_s = reverse_string(test_string)
    print(f"Original: {test_string}")
    print(f"Reversed: {reversed_s}")
