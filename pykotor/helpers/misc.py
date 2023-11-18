from __future__ import annotations

import hashlib
import platform
import sys
from enum import Enum
from typing import TYPE_CHECKING

from pykotor.helpers.path import Path

if TYPE_CHECKING:
    import os
    from xml.etree.ElementTree import Element


class ProcessorArchitecture(Enum):
    BIT_32 = "32bit"
    BIT_64 = "64bit"

    def __str__(self):
        return f"{self.value}bit"

    @classmethod
    def from_os(cls):
        return ProcessorArchitecture(platform.architecture()[0])

    @classmethod
    def from_python(cls):
        return ProcessorArchitecture.BIT_64 if sys.maxsize > 2**32 else ProcessorArchitecture.BIT_32

    def get_machine_repr(self):
        if ProcessorArchitecture.BIT_32:
            return "x86"
        if ProcessorArchitecture.BIT_64:
            return "x64"
        return None

    def get_int(self):
        if ProcessorArchitecture.BIT_32:
            return 32
        if ProcessorArchitecture.BIT_64:
            return 64
        return None

    def get_dashed_bitness(self):
        if ProcessorArchitecture.BIT_32:
            return "32-bit"
        if ProcessorArchitecture.BIT_64:
            return "64-bit"
        return None

    def supports_64_bit(self) -> bool:
        """Check if the architecture supports 64-bit processing."""
        return self == ProcessorArchitecture.BIT_64


def has_attr_excluding_object(cls, attr_name) -> bool:
    # Exclude the built-in 'object' class
    mro_classes = [c for c in cls.mro() if c != object]

    return any(attr_name in base_class.__dict__ for base_class in mro_classes)


def is_class_or_subclass_but_not_instance(cls, target_cls) -> bool:
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance, target_cls) -> bool:
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class type, always return False
    # instance is not a class
    return type(instance) is target_cls or is_class_or_subclass_but_not_instance(type(instance), target_cls)


def generate_filehash_sha256(filepath: os.PathLike | str) -> str:
    sha1_hash = hashlib.sha256()
    filepath = filepath if isinstance(filepath, Path) else Path(filepath)
    with filepath.open("rb") as f:
        data = f.read(65536)
        while data:  # read in 64k chunks
            sha1_hash.update(data)
            data = f.read(65536)
    return sha1_hash.hexdigest()


def indent(elem: Element, level=0):
    """Indents the XML element by the given level
    Args:
        elem: Element - The element to indent
        level: int - The level of indentation (default: 0).

    Returns
    -------
        None - Indents the element in-place
    Processing Logic:
        - Calculate indentation string based on level
        - If element is empty, set text to indentation
        - If no tail, set tail to newline + indentation
        - Recursively indent child elements with increased level
        - If no tail after children, set tail to indentation
        - If level and no tail, set tail to indentation.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = f"{i}  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for e in elem:
            indent(e, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i