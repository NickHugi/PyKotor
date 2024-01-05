from __future__ import annotations

import hashlib
import os
import platform
import sys
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

from utility.path import Path

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element


class ProcessorArchitecture(Enum):
    BIT_32 = "32bit"
    BIT_64 = "64bit"

    def __str__(self):
        return self.value

    def __int__(self):
        return self.get_int() or -1

    @classmethod
    def from_os(cls):
        return cls(platform.architecture()[0])

    @classmethod
    def from_python(cls):
        return cls.BIT_64 if sys.maxsize > 2**32 else cls.BIT_32

    def get_machine_repr(self):
        if self == self.BIT_32:
            return "x86"
        if self == self.BIT_64:
            return "x64"
        return None

    def get_int(self):
        if self == self.BIT_32:
            return 32
        if self == self.BIT_64:
            return 64
        return None

    def get_dashed_bitness(self):
        if self == self.BIT_32:
            return "32-bit"
        if self == self.BIT_64:
            return "64-bit"
        return None

    def supports_64_bit(self) -> bool:
        """Check if the architecture supports 64-bit processing."""
        return self == self.BIT_64

def format_gpu_info(info, headers):
    # Determine the maximum width for each column
    column_widths: list[int] = [max(len(str(row[i])) for row in [headers, *info]) for i in range(len(headers))]

    # Function to format a single row
    def format_row(row) -> str:
        return " | ".join(f"{str(item).ljust(column_widths[i])}" for i, item in enumerate(row))

    # Build the output string
    output: str = format_row(headers) + "\n"
    output += "-" * (sum(column_widths) + len(headers) * 3 - 1) + "\n"  # Add a separator line

    # Append each row of GPU details to the output string
    for row in info:
        output += format_row(row) + "\n"

    return output

T = TypeVar("T")
def remove_duplicates(my_list: list[T], *, case_insensitive=False) -> list[T]:
    seen = set()
    return [
        x.lower() if case_insensitive and isinstance(x, str) else x
        for x in my_list
        if not (x in seen or seen.add(x))
    ]

def get_system_info():
    # sourcery skip: extract-method, list-comprehension, merge-dict-assign
    info = {}

    # Basic OS information
    info["Platform"] = platform.system()
    info["Platform-Release"] = platform.release()
    info["Platform-Version"] = platform.version()
    info["Architecture"] = platform.machine()

    # CPU information
    psutil = None
    with suppress(ImportError):
        import psutil
    if psutil is not None:
        info["Physical cores"] = psutil.cpu_count(logical=False)
        info["Total cores"] = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        info["Max Frequency"] = f"{cpu_freq.max:.2f}Mhz"
        info["Min Frequency"] = f"{cpu_freq.min:.2f}Mhz"
        info["Current Frequency"] = f"{cpu_freq.current:.2f}Mhz"
        info["CPU Usage Per Core"] = [f"{x}%" for x in psutil.cpu_percent(percpu=True, interval=1)]
        info["Total CPU Usage"] = f"{psutil.cpu_percent()}%"

        # RAM Information
        svmem = psutil.virtual_memory()
        info["Total Memory"] = f"{svmem.total / (1024 ** 3):.2f} GB"
        info["Available Memory"] = f"{svmem.available / (1024 ** 3):.2f} GB"
        info["Used Memory"] = f"{svmem.used / (1024 ** 3):.2f} GB"
        info["Memory Usage"] = f"{svmem.percent}%"

    # GPU Information
    GPUtil = None
    with suppress(ImportError):
        import GPUtil
    if GPUtil is not None:
        gpus = GPUtil.getGPUs()
        gpu_info = []
        for gpu in gpus:
            gpu_info.append((
                gpu.id, gpu.name, f"{gpu.memoryTotal}MB", f"{gpu.memoryUsed}MB",
                f"{gpu.memoryFree}MB", f"{gpu.driver}", f"{gpu.temperature} C",
            ))
        info["GPU Details"] = format_gpu_info(gpu_info, headers=("id", "name", "total memory", "used memory", "free memory", "driver", "temperature"))

    return info
def is_debug_mode() -> bool:
    ret = False
    if os.getenv("PYTHONDEBUG", None):
        ret = True
    if os.getenv("DEBUG_MODE", "0") == "1":
        ret = True
    if hasattr(sys, "gettrace") and sys.gettrace() is not None:
        ret = True
    print(f"DEBUG MODE: {ret}")
    return ret

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


def generate_sha256_hash(
    data_input: bytes | bytearray | memoryview | os.PathLike | str,
    chunk_size: int = 65536,
) -> str:
    sha256_hash = hashlib.sha256()

    def process_chunk(data):
        sha256_hash.update(data)

    if isinstance(data_input, (bytes, bytearray, memoryview)):
        # Process the byte-like data in chunks of 65536 bytes
        for start in range(0, len(data_input), chunk_size):
            end = start + chunk_size
            process_chunk(data_input[start:end])
    else:
        # Handle file path input
        if not isinstance(data_input, (os.PathLike, str)):
            msg = "Input must be bytes, bytearray, memoryview, or a path-like object"
            raise TypeError(msg)

        with Path.pathify(data_input).open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                process_chunk(chunk)

    return sha256_hash.hexdigest()


def indent(elem: Element, level=0):
    """Indents the XML element by the given level
    Args:
        elem: Element - The element to indent
        level: int - The level of indentation (default: 0).

    Returns
    -------
        None - Indents the element in-place

    Processing Logic:
    ----------------
        - Calculate indentation string based on level
        - If element is empty, set text to indentation
        - If no tail, set tail to newline + indentation
        - Recursively indent child elements with increased level
        - If no tail after children, set tail to indentation
        - If level and no tail, set tail to indentation.
    """
    i: str = "\n" + level * "  "
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


def is_int(string: str) -> bool:
    """Can be cast to an int without raising an error.

    Args:
    ----
        string (str):

    """
    try:
        _ = int(string)
    except ValueError:
        return False
    else:
        return True


def is_float(string: str) -> bool:
    """Can be cast to a float without raising an error.

    Args:
    ----
        string (str):

    """
    try:
        _ = float(string)
    except ValueError:
        return False
    else:
        return True
