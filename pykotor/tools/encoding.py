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
