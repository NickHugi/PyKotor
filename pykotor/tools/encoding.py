from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

import charset_normalizer

if TYPE_CHECKING:
    from pykotor.common.language import Language


def decode_bytes_with_fallbacks(
    byte_content: bytes,
    errors="strict",
    encoding: str | None = None,
    lang: Language | None = None,
) -> str:
    """A well rounded decoding function used to decode byte content with provided language/encoding information. If an exact match cannot be
    determined, it will use heuristics based on what is known, to determine what encoding to use. Utilizes the charset_normalizer library internally.

    Args:
    ----
        byte_content (bytes): the bytes to decode
        errors (str): When detection fails, this determines how to decode the ultimate fallback encoding. Same variable sent to the builtin decode() function.
        lang (Language): The language of the bytes being decoded, if known.
    """
    provided_encoding = encoding or (lang.get_encoding() if lang else None)
    if provided_encoding:
        with contextlib.suppress(UnicodeDecodeError):
            return byte_content.decode(provided_encoding, errors=errors)

    detected_encoding = charset_normalizer.from_bytes(byte_content).best()
    if detected_encoding:
        encoding = detected_encoding.encoding

        # Special handling for UTF-8 BOM
        if detected_encoding.byte_order_mark and "utf-8" in encoding.replace("_", "-"):  # covers 'utf-8', 'utf_8', etc.
            encoding = "utf-8-sig"

        return byte_content.decode(encoding=encoding, errors=errors)
    return byte_content.decode(errors=errors)


def find_best_8bit_encoding(s: str) -> str | None:
    """Finds the best 8-bit encoding for a string
    Args:
        s: str - The input string to analyze
    Returns:
        str | None - The detected 8-bit encoding or None if no match found
    - The string is first encoded to UTF-8 bytes
    - The byte string is analyzed to find potential charset matches
    - Non 8-bit and Unicode matches are filtered out
    - If any 8-bit matches remain, the one with the highest confidence is returned
    - If no 8-bit matches, None is returned.
    """
    # First, we encode the string to UTF-8 bytes. Python str objects are inherently Unicode.
    utf8_encoded = s.encode("utf-8")

    # Then, we try to find the best match for this byte string
    # assuming it was originally encoded with an unknown 8-bit charset
    matches = charset_normalizer.from_bytes(utf8_encoded)

    # We filter out non 8-bit encodings and Unicode encodings
    eight_bit_encodings: list[charset_normalizer.CharsetMatch] = [match for match in matches if "iso" in match.encoding.lower() or match.encoding.startswith("cp") or match.encoding.startswith("windows-")]

    # If we have 8-bit matches, we take the one with the highest confidence
    if eight_bit_encodings:
        best_match: charset_normalizer.CharsetMatch = max(eight_bit_encodings, key=lambda m: m.chaos)
        return best_match.encoding

    return None
