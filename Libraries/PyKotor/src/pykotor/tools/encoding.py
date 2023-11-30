from __future__ import annotations

import codecs
import contextlib
from typing import TYPE_CHECKING

import charset_normalizer

if TYPE_CHECKING:
    from pykotor.common.language import Language


def get_single_byte_charset(encoding) -> list[str]:
    charset = []
    for i in range(256):
        try:
            char = codecs.decode(bytes([i]), encoding)
            charset.append(char)
        except UnicodeDecodeError:  # noqa: PERF203
            charset.append("")  # Append a blank for non-existent characters
    return charset

def get_double_byte_charset(encoding) -> list[str]:
    # I believe these need to be mapped to the TXI with the 'dbmapping' field. Experimentation would be required for the syntax, perhaps could pull from other aurora games.
    charset = []
    if encoding == "cp936":
        for i in range(256):
            if 0x00 <= i <= 0x7F:
                # Single-byte code
                try:
                    char = codecs.decode(bytes([i]), encoding)
                    charset.append(char)
                except UnicodeDecodeError:
                    charset.append("")  # Append a blank for non-existent characters
            elif 0x81 <= i <= 0x9F:
                # Double-byte introducer, skip this byte
                #continue
                charset.append("")  # Undefined code point, append a blank
            elif 0xA1 <= i <= 0xDF:
                # Single-byte code
                try:
                    char = codecs.decode(bytes([i]), encoding)
                    charset.append(char)
                except UnicodeDecodeError:
                    charset.append("")  # Append a blank for non-existent characters
            elif 0xE0 <= i <= 0xFC:
                # Double-byte introducer, the second byte can be any of the 256 possible values
                for j in range(256):
                    try:
                        char = codecs.decode(bytes([i, j]), encoding)
                        charset.append(char)
                    except UnicodeDecodeError:  # noqa: PERF203
                        charset.append("")  # Append a blank for non-existent characters
            else:
                charset.append("")  # Undefined code point, append a blank
    elif encoding == "cp949":
        for i in range(256):
            # Adjusted ranges based on IBM-949 encoding structure
            if 0x00 <= i <= 0x7F or 0xA1 <= i <= 0xDF or 0x9A <= i <= 0xA0:
                # Single-byte code
                try:
                    char = codecs.decode(bytes([i]), encoding)
                    charset.append(char)
                except UnicodeDecodeError:
                    charset.append("")  # Append a blank for non-existent characters
            elif 0x81 <= i <= 0x9F or i == 0xC9 or i == 0xFE:
                # User-defined ranges or double-byte introducer
                charset.append("")  # Placeholder for user-defined ranges
            elif 0xE0 <= i <= 0xFC or 0x8F <= i <= 0x99:
                # Double-byte introducer, the second byte can be any of the 256 possible values
                for j in range(256):
                    try:
                        char = codecs.decode(bytes([i, j]), encoding)
                        charset.append(char)
                    except UnicodeDecodeError:  # noqa: PERF203
                        charset.append("")  # Append a blank for non-existent characters
            else:
                charset.append("")  # Undefined code point, append a blank
    elif encoding == "cp950":
        # Include single-byte graphical characters (standard ASCII + additional characters)
        for i in range(256):
            if i <= 0x7F or i == 0xA1:  # ASCII range and single-byte euro sign
                try:
                    char = chr(i)  # Direct ASCII mapping
                    charset.append(char)
                except ValueError:
                    charset.append("")  # Append a blank for invalid values
            elif 0x81 <= i <= 0xFE:  # Double-byte character lead byte
                for j in range(256):
                    if (0x40 <= j <= 0x7E) or (0xA1 <= j <= 0xFE):
                        # Apply formula based on Big5 to Unicode PUA mapping
                        unicode_val: int = -1  # Placeholder for ranges not covered
                        if 0x81 <= i <= 0x8D:
                            unicode_val = 0xeeb8 + (157 * (i - 0x81)) + (j - 0x40 if j < 0x80 else j - 0x62)
                        elif 0x8E <= i <= 0xA0:
                            unicode_val = 0xe311 + (157 * (i - 0x8E)) + (j - 0x40 if j < 0x80 else j - 0x62)
                        elif 0xC6 <= i <= 0xC8:
                            unicode_val = 0xf672 + (157 * (i - 0xC6)) + (j - 0x40 if j < 0x80 else j - 0x62)
                        elif 0xFA <= i <= 0xFE:
                            unicode_val = 0xe000 + (157 * (i - 0xFA)) + (j - 0x40 if j < 0x80 else j - 0x62)

                        if unicode_val != -1:
                            try:
                                char = chr(unicode_val)
                                charset.append(char)
                            except ValueError:
                                charset.append("")  # Append a blank for invalid Unicode values
                    else:
                        charset.append("")  # Append a blank for bytes not in the valid range
            else:
                charset.append("")  # Append a blank for bytes outside the Big5 range
    else:  # maybe possible?
        single_byte_end = 0x7F  # End of single-byte range
        potential_lead_byte_start = 0x81  # Start of potential lead byte range for double-byte characters
        potential_lead_byte_end = 0xFC  # End of potential lead byte range

        for i in range(256):
            if i <= single_byte_end or (0xA1 <= i <= 0xDF):  # Single-byte characters
                try:
                    char = bytes([i]).decode(encoding)
                    charset.append(char)
                except UnicodeDecodeError:
                    charset.append("")  # Append a blank for non-existent characters

            elif potential_lead_byte_start <= i <= potential_lead_byte_end:  # Potential lead byte for double-byte characters
                for j in range(256):
                    try:
                        char = bytes([i, j]).decode(encoding)
                        charset.append(char)
                    except UnicodeDecodeError:  # noqa: PERF203
                        charset.append("")  # Append a blank for non-existent characters
            else:
                charset.append("")  # For bytes outside the valid range
    return charset

def get_charset_from_encoding(encoding):
    charset = []
    #for i in range(0x110000):
    for i in range(256):
        try:
            char = bytes([i]).decode(encoding)
            charset.append(char)
        except UnicodeDecodeError:  # noqa: PERF203
            charset.append("")
    return charset

def decode_bytes_with_fallbacks(
    byte_content: bytes,
    errors="strict",
    encoding: str | None = None,
    lang: Language | None = None,
    only_8bit_encodings: bool | None = False,
) -> str:
    """A well rounded decoding function used to decode byte content with provided language/encoding information. If an exact match cannot be
    determined, it will use heuristics based on what is known, to determine what encoding to use. Utilizes the charset_normalizer library internally.

    Args:
    ----
        byte_content (bytes): the bytes to decode
        errors (str): When detection fails, this determines how to decode the ultimate fallback encoding. Same variable sent to the builtin decode() function.
        lang (Language): The language of the bytes being decoded, if known.
    """
    # Store the detections as there's no need to recalc
    detected_encodings: charset_normalizer.CharsetMatches | None = None

    def _decode_attempt(attempt_errors) -> str:
        nonlocal detected_encodings
        provided_encoding: str | None = encoding or (lang.get_encoding() if lang else None)

        # Attempt decoding with provided encoding
        if provided_encoding:
            with contextlib.suppress(UnicodeDecodeError):
                return byte_content.decode(provided_encoding, errors=attempt_errors)

        # Detect encoding using charset_normalizer
        detected_encodings = detected_encodings or charset_normalizer.from_bytes(byte_content)

        # Filter the charset-normalizer results to encodings with a maximum of 256 characters
        if only_8bit_encodings:
            max_8bit_characters = 256
            detected_8bit_encodings: list[charset_normalizer.CharsetMatch] = [enc for enc in detected_encodings if len(enc.alphabets) <= max_8bit_characters]
            best_match: charset_normalizer.CharsetMatch = detected_8bit_encodings[0]
            best_8bit_encoding: str = best_match.encoding or "windows-1252"
            return byte_content.decode(encoding=best_8bit_encoding, errors=attempt_errors)

        result_detect: charset_normalizer.CharsetMatch | None = detected_encodings.best()

        if result_detect:
            best_encoding: str = result_detect.encoding

            # Special handling for BOM
            aliases: list[str] = result_detect.encoding_aliases
            if result_detect.bom:
                aliases.append(best_encoding)
                for alias in aliases:
                    normalized_alias = alias.replace("_", "-")
                    if normalized_alias.startswith("utf-"):
                        best_encoding=f"{best_encoding}-sig"
                        break

            return byte_content.decode(encoding=best_encoding, errors=attempt_errors)

        # Final fallback if no encoding is detected
        return byte_content.decode(errors=attempt_errors)

    # Attempt strict first for more accurate results.
    with contextlib.suppress(UnicodeDecodeError):
        return _decode_attempt(attempt_errors="strict")
    return _decode_attempt(attempt_errors=errors)
