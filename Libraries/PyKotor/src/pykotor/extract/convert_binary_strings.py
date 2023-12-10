from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.absolute().parent.parent))

from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY


def singlequote_byte_string_to_triplequote_byte_string(single_line_str: str) -> str:
    # Convert escaped characters into actual characters
    return single_line_str.replace("\\\\", "\\")


def triplequote_byte_string_to_singlequote_byte_string(readable_str: str) -> str:
    # Convert actual characters back to their escaped versions
    return readable_str.replace("\\", "\\\\")


def bytes_to_singlequote_byte_string(input_bytes: bytes) -> str:
    return input_bytes.decode("utf-8", errors="ignore")


def bytes_to_triplequote_byte_string(input_bytes: bytes) -> str:
    return input_bytes.decode("unicode_escape", errors="ignore")


def triplequote_byte_string_to_bytes(readable_str: str) -> bytes:
    return bytes(readable_str, "utf-8", errors="ignore")


def singlequote_byte_string_to_bytes(readable_str: str) -> bytes:
    return bytes(readable_str, "unicode_escape", errors="ignore")


def highlight_difference(
    key: str,
    original_string: str,
    converted_string: str,
    reverted_string: str,
) -> bool:
    """Compare two binary strings and highlight the first difference."""
    min_length = min(len(original_string), len(reverted_string))
    for i in range(min_length):
        if original_string[i] != reverted_string[i]:
            # Extract 10 characters before and after the mismatch
            start = max(0, i - 50)
            end = min(min_length, i + 50 + 1)

            # Represent special characters in a readable manner
            original_char = repr(original_string[i])  # Using repr to represent special characters
            converted_char = repr(converted_string[i])
            reverted_char = repr(reverted_string[i])

            # Extract excerpts and place arrows around differing character
            original_excerpt = repr(f"{original_string[start:i]}>>>{original_char  }<<<{original_string[ i + 1:end]}")[1:-1]
            converted_excerpt = repr(f"{converted_string[start:i]}>>>{converted_char}<<<{converted_string[i + 1:end]}")[1:-1]
            reverted_excerpt = repr(f"{reverted_string[start:i]}>>>{reverted_char  }<<<{reverted_string[ i + 1:end]}")[1:-1]

            # Represent special characters in a readable manner
            original_char = repr(
                original_string[i],
            )  # Using repr to represent special characters
            reverted_char = repr(reverted_string[i])

            # Display the excerpts
            print(f"{key}:", "FAILED!")
            print(f"    Difference found at character position {i+1:,}.")
            print(f"    Original character:  {original_char }")
            print(f"    Converted character: {converted_char}")
            print(f"    Reverted character:  {reverted_char }")
            print(f"    Printing {i-start} characters before and {end-i-1} characters after the difference:")
            print(f"    Original:  {original_excerpt}")
            print(f"    Converted: {converted_excerpt}")
            print(f"    Reverted:  {reverted_excerpt}")
            return False

    # If we haven't returned yet, then either the strings are identical
    # or one string is shorter than the other.
    if len(original_string) != len(reverted_string):
        print()
        print(f"{key}: The strings have different lengths.")
        print("Original  length:", len(original_string))
        print("Converted length:", len(converted_string))
        print("Reverted  length:", len(reverted_string))
        print()
        return False

    return True


def test_before_write_file(
    key: str,
    original_string: str,
    original_bytes: bytes,
    converted_string: str,
    converted_bytes: bytes,
    reverted_string: str,
) -> bool:
    return_bool = character_positional_check_result = highlight_difference(
        key,
        original_string,
        converted_string,
        reverted_string,
    )
    equality_check = original_bytes == converted_bytes
    return_bool &= equality_check
    if not equality_check:
        print(f"    original_bytes {'==' if equality_check else '!='} converted_bytes")
    equality_check = original_string == converted_string
    return_bool &= equality_check
    if character_positional_check_result:
        print(f"{key}:", "success" if equality_check else equality_check)
    if not equality_check:
        print(f"    original_string {'==' if equality_check else '!='} converted_string")
    if not return_bool:
        print()
    return return_bool


def write_dictionary_to_py_file(
    dictionary: dict,
    dict_name: str,
    output_filepath: Path,
):  # sourcery skip: use-dict-items
    output_message = f"Writing converted dictionary {dict_name} to '{file_path}'"
    print(
        os.linesep,
        "#" * len(output_message) + os.linesep,
        os.linesep,
        output_message + os.linesep,
        os.linesep,
        "#" * len(output_message),
        os.linesep,
    )
    with output_filepath.open("a", encoding="utf-8", newline="\r\n") as file:
        file.write(f"{dict_name} = {{{os.linesep}")
        for key in dictionary:
            original_binary_data: bytes = dictionary[key]
            original_literal_binary_string: str = bytes_to_singlequote_byte_string(original_binary_data)
            converted_literal_binary_string: str = singlequote_byte_string_to_triplequote_byte_string(
                original_literal_binary_string,
            )
            converted_binary_data: bytes = triplequote_byte_string_to_bytes(converted_literal_binary_string)
            reverted_literal_binary_string: str = bytes_to_triplequote_byte_string(converted_binary_data)
            # reverted_binary_data: bytes = singlequote_byte_string_to_bytes(reverted_literal_binary_string)  # noqa: ERA001
            if test_before_write_file(
                key,
                original_literal_binary_string,
                original_binary_data,
                converted_literal_binary_string,
                converted_binary_data,
                reverted_literal_binary_string,
            ):
                file.write(f"    '{key}': b'''{converted_literal_binary_string}''',{os.linesep}")
            else:
                file.write(f"    '{key}': b'{reverted_literal_binary_string}',{os.linesep}")

        file.write(f"}}{os.linesep}")


file_path = Path(".\\scriptlib_formatted.py")
if file_path.exists():
    print(f"Overwriting {file_path} with converted dictionaries...")
    file_path.unlink()
write_dictionary_to_py_file(
    KOTOR_LIBRARY,
    dict_name="KOTOR_LIBRARY",
    output_filepath=file_path,
)
write_dictionary_to_py_file(
    TSL_LIBRARY,
    dict_name="TSL_LIBRARY",
    output_filepath=file_path,
)
print()
print(f"Finished writing conversions to '{file_path.resolve()}'")
