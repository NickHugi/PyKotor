from typing import List


def get_nums(string_input: str) -> List[int]:
    """
    Returns the numbers stored within a string. Numbers in a string are seperated by any non-numeric character.

    Args:
        string_input: String to search.

    Returns:
        List of numbers.
    """
    string = ""
    nums = []
    for char in string_input + " ":
        if char.isdigit():
            string += char
        elif string != "":
            nums.append(int(string))
            string = ""
    return nums
