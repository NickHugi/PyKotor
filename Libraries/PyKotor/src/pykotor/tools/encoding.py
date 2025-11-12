from __future__ import annotations

import codecs

from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

    from charset_normalizer import CharsetMatch, CharsetMatches

    from pykotor.common.language import Language

charset_normalizer: None | ModuleType
try:
    import charset_normalizer
except ImportError:
    charset_normalizer = None


def decode_bytes_with_fallbacks(  # noqa: C901
    byte_content: bytes | bytearray,
    errors: str = "strict",
    encoding: str | None = None,
    lang: Language | None = None,
    only_8bit_encodings: bool | None = False,  # noqa: FBT002
) -> str:
    """A well rounded decoding function used to decode byte content with provided language/encoding information.

    If an exact match cannot be determined, this function will use heuristics
    based on what is known, to determine what encoding to use. Utilizes the charset_normalizer library internally.

    Args:
    ----
        byte_content (bytes): the bytes to decode
        errors (str): When detection fails, this determines how to decode the ultimate fallback encoding. Same variable sent to the builtin decode() function.
        lang (Language): The language of the bytes being decoded, if known. Used to determine encoding.
        encoding (str): The encoding to use. If set to None, will auto-detect. If this arg is defined, the lang arg will be ignored.
        only_8bit_encodings (bool): If true, will force the best SBCS (single-byte) encoding to be used. Defaults to False.

    Returns:
    -------
        str - Decoded string

    References:
    ----------
        vendor/KotOR.js (Character encoding handling in JavaScript)
        Note: KotOR uses multiple character encodings including ASCII, UTF-8, and language-specific encodings

    Processing Logic:
    ----------------
        - If charset_normalizer not installed, use built-in decoding logic.
        - Attempt decoding with provided encoding
        - Detect encoding using charset_normalizer if no encoding provided
        - Filter detections to max 256 characters if only_8bit_encodings
        - Decode with best detected encoding
        - Try strict errors first, then fallback errors handling
    """
    provided_encoding: str | None = encoding or (lang.get_encoding() if lang else None)
    if provided_encoding is not None:
        # Try decoding with provided encoding, but fall back to auto-detection if it fails
        with suppress(UnicodeDecodeError):
            return byte_content.decode(encoding=provided_encoding, errors=errors)
        # If provided encoding fails, fall through to auto-detection
        provided_encoding = None
    if charset_normalizer is None:
        if provided_encoding is None:
            provided_encoding = "windows-1252" if only_8bit_encodings else "utf-8"
        return byte_content.decode(encoding=provided_encoding, errors=errors)

    # Store the detections as there's no need to recalc
    detected_encodings: CharsetMatches | None = None

    def _decode_attempt(attempt_errors: str) -> str:
        nonlocal detected_encodings

        # Attempt decoding with provided encoding
        if provided_encoding is not None:
            with suppress(UnicodeDecodeError):
                return byte_content.decode(provided_encoding, errors=attempt_errors)

        # Detect encoding using charset_normalizer
        detected_encodings = detected_encodings or charset_normalizer.from_bytes(byte_content)  # pyright: ignore[reportOptionalMemberAccess]

        if detected_encodings is None:
            # Semi-Final fallback (utf-8) if no encoding is detected
            with suppress(UnicodeDecodeError):
                return byte_content.decode(encoding="utf-8", errors=attempt_errors)
            # Final fallback (latin1) if no encoding is detected
            return byte_content.decode(encoding="latin1", errors=attempt_errors)

        # Filter the charset-normalizer results to encodings with a maximum of 256 characters
        if only_8bit_encodings:
            max_8bit_characters: int = 256
            detected_8bit_encodings: list[CharsetMatch] = [enc_match for enc_match in detected_encodings if len(enc_match.alphabets) <= max_8bit_characters]
            best_8bit_encoding = "windows-1252"
            if detected_8bit_encodings:
                best_match: CharsetMatch = detected_8bit_encodings[0]
                best_8bit_encoding: str = best_match.encoding
            return byte_content.decode(encoding=best_8bit_encoding, errors=attempt_errors)

        result_detect: CharsetMatch | None = detected_encodings.best()
        if result_detect is None:
            # Semi-Final fallback (utf-8) if no encoding is detected
            with suppress(UnicodeDecodeError):
                return byte_content.decode(encoding="utf-8", errors=attempt_errors)
            # Final fallback (latin1) if no encoding is detected
            return byte_content.decode(encoding="latin1", errors=attempt_errors)

        best_encoding: str = result_detect.encoding

        # Special handling for BOM
        aliases: set[str] = {alias.lower() for alias in result_detect.encoding_aliases}
        aliases.add(best_encoding.lower())
        if result_detect.bom:
            for alias in aliases:
                normalized_alias: str = alias.replace("_", "-")
                if normalized_alias.startswith("utf-8"):
                    best_encoding = "utf-8-sig"
                    break
                if normalized_alias.startswith("utf-16"):
                    best_encoding = "UTF-16LE"
                    break

        # Check all detected encodings and prioritize UTF-8 if it's detected
        for match in detected_encodings:
            match_aliases: set[str] = {alias.lower() for alias in match.encoding_aliases}
            match_aliases.add(match.encoding.lower())
            if "utf-8" in match_aliases or match.encoding.lower() in {"utf-8", "utf8"}:
                with suppress(UnicodeDecodeError):
                    return byte_content.decode(encoding="utf-8", errors=attempt_errors)

        # Try UTF-8 first if it's a valid detection, as it's more common and reliable
        if "utf-8" in aliases or best_encoding.lower() in {"utf-8", "utf8"}:
            with suppress(UnicodeDecodeError):
                return byte_content.decode(encoding="utf-8", errors=attempt_errors)

        return byte_content.decode(encoding=best_encoding, errors=attempt_errors)

    # Attempt strict first for more accurate results.
    with suppress(UnicodeDecodeError):
        return _decode_attempt(attempt_errors="strict")
    return _decode_attempt(attempt_errors=errors)


def get_charset_from_singlebyte_encoding(
    encoding: str,
    *,
    indexing: bool = True,
) -> list[str]:
    charset: list[str] = []
    for i in range(256):
        try:
            charset.append(bytes([i]).decode(encoding))
        except UnicodeDecodeError:  # noqa: PERF203
            if indexing:
                charset.append("")
    return charset


def get_charset_from_unicode_encoding(
    encoding: str,
    *,
    indexing: bool = True,
) -> list[str]:
    charset: list[str] = []
    for i in range(0x110000):
        try:
            charset.append(bytes([i]).decode(encoding))
        except UnicodeDecodeError:  # noqa: PERF203
            if indexing:
                charset.append("")
    return charset


def get_charset_from_doublebyte_encoding(
    encoding: str,
) -> list[str]:
    # I believe these need to be mapped to the TXI with the 'dbmapping' field.
    # Experimentation would be required for the syntax, perhaps could pull from other aurora games.
    if encoding == "cp936":
        return get_cp936_charset()
    if encoding == "cp949":
        return get_cp949_charset()
    if encoding == "cp950":
        return get_cp950_charset()

    # maybe possible?
    return get_generalized_doublebyte_charset(encoding)


def get_cp950_charset() -> list[str]:  # noqa: C901, PLR0912
    charset: list[str] = []
    # Include single-byte graphical characters (standard ASCII + additional characters)
    for i in range(256):
        if i <= 0x7F or i == 0xA1:  # ASCII range and single-byte euro sign  # noqa: PLR2004
            try:
                charset.append(chr(i))  # Direct ASCII mapping
            except ValueError:
                charset.append("")  # Append a blank for invalid values
        elif 0x81 <= i <= 0xFE:  # Double-byte character lead byte  # noqa: PLR2004
            for j in range(256):
                if (0x40 <= j <= 0x7E) or (0xA1 <= j <= 0xFE):  # noqa: PLR2004
                    # Apply formula based on Big5 to Unicode PUA mapping
                    unicode_val: int = -1  # Placeholder for ranges not covered
                    if 0x81 <= i <= 0x8D:  # noqa: PLR2004
                        unicode_val = 0xEEB8 + (157 * (i - 0x81)) + (j - 0x40 if j < 0x80 else j - 0x62)  # noqa: PLR2004
                    elif 0x8E <= i <= 0xA0:  # noqa: PLR2004
                        unicode_val = 0xE311 + (157 * (i - 0x8E)) + (j - 0x40 if j < 0x80 else j - 0x62)  # noqa: PLR2004
                    elif 0xC6 <= i <= 0xC8:  # noqa: PLR2004
                        unicode_val = 0xF672 + (157 * (i - 0xC6)) + (j - 0x40 if j < 0x80 else j - 0x62)  # noqa: PLR2004
                    elif 0xFA <= i <= 0xFE:  # noqa: PLR2004
                        unicode_val = 0xE000 + (157 * (i - 0xFA)) + (j - 0x40 if j < 0x80 else j - 0x62)  # noqa: PLR2004

                    if unicode_val != -1:
                        try:
                            charset.append(chr(unicode_val))
                        except ValueError:
                            charset.append("")  # Append a blank for invalid Unicode values
                else:
                    charset.append("")  # Append a blank for bytes not in the valid range
        else:
            charset.append("")  # Append a blank for bytes outside the Big5 range
    return charset


def get_cp949_charset() -> list[str]:
    charset: list[str] = []
    for i in range(256):
        # Adjusted ranges based on IBM-949 encoding structure
        if 0x00 <= i <= 0x7F or 0xA1 <= i <= 0xDF or 0x9A <= i <= 0xA0:  # noqa: PLR2004
            # Single-byte code
            try:
                charset.append(codecs.decode(bytes([i]), "cp949"))
            except UnicodeDecodeError:
                charset.append("")  # Append a blank for non-existent characters
        elif 0x81 <= i <= 0x9F or i in (0xC9, 0xFE):  # noqa: PLR2004
            # User-defined ranges or double-byte introducer
            charset.append("")  # Placeholder for user-defined ranges
        elif 0xE0 <= i <= 0xFC or 0x8F <= i <= 0x99:  # noqa: PLR2004
            # Double-byte introducer, the second byte can be any of the 256 possible values
            for j in range(256):
                try:
                    charset.append(codecs.decode(bytes([i, j]), "cp949"))
                except UnicodeDecodeError:  # noqa: PERF203
                    charset.append("")  # Append a blank for non-existent characters
        else:
            charset.append("")  # Undefined code point, append a blank
    return charset


def get_cp936_charset() -> list[str]:
    # sourcery skip: merge-duplicate-blocks, remove-redundant-if
    charset: list[str] = []
    for i in range(256):
        if 0x00 <= i <= 0x7F:  # noqa: PLR2004
            # Single-byte code
            try:
                charset.append(codecs.decode(bytes([i]), "cp936"))
            except UnicodeDecodeError:
                charset.append("")  # Append a blank for non-existent characters
        elif 0x81 <= i <= 0x9F:  # noqa: PLR2004
            # Double-byte introducer, skip this byte
            # continue
            charset.append("")  # Undefined code point, append a blank
        elif 0xA1 <= i <= 0xDF:  # noqa: PLR2004
            # Single-byte code
            try:
                charset.append(codecs.decode(bytes([i]), "cp936"))
            except UnicodeDecodeError:
                charset.append("")  # Append a blank for non-existent characters
        elif 0xE0 <= i <= 0xFC:  # noqa: PLR2004
            # Double-byte introducer, the second byte can be any of the 256 possible values
            for j in range(256):
                try:
                    charset.append(codecs.decode(bytes([i, j]), "cp936"))
                except UnicodeDecodeError:  # noqa: PERF203
                    charset.append("")  # Append a blank for non-existent characters
        else:
            charset.append("")  # Undefined code point, append a blank
    return charset


def get_generalized_doublebyte_charset(
    encoding: str,
) -> list[str]:
    charset: list[str] = []

    single_byte_end: int = 0x7F  # End of single-byte range
    potential_lead_byte_start: int = 0x81  # Start of potential lead byte range for double-byte characters
    potential_lead_byte_end: int = 0xFC  # End of potential lead byte range

    for i in range(256):
        if i <= single_byte_end or (0xA1 <= i <= 0xDF):  # Single-byte characters  # noqa: PLR2004
            try:
                charset.append(bytes([i]).decode(encoding))
            except UnicodeDecodeError:
                charset.append("")  # Append a blank for non-existent characters

        elif potential_lead_byte_start <= i <= potential_lead_byte_end:  # Potential lead byte for double-byte characters
            for j in range(256):
                try:
                    charset.append(bytes([i, j]).decode(encoding))
                except UnicodeDecodeError:  # noqa: PERF203
                    charset.append("")  # Append a blank for non-existent characters
        else:
            charset.append("")  # For bytes outside the valid range
    return charset
