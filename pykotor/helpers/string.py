def ireplace(original, target, replacement):
    if not original or not target:
        return original
    # Initialize an empty result string and a pointer to traverse the original string
    result = ""
    i = 0

    # Length of the target string
    target_length = len(target)

    # Convert the target to lowercase for case-insensitive comparison
    target_lower = target.lower()

    while i < len(original):
        # If a potential match is found
        if original[i : i + target_length].lower() == target_lower:
            # Add the replacement to the result
            result += replacement
            # Skip the characters of the target
            i += target_length
        else:
            # Add the current character to the result
            result += original[i]
            i += 1
    return result
