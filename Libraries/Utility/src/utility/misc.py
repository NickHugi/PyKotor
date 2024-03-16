from __future__ import annotations

import hashlib
import os
import platform
import sys

from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING, SupportsFloat, SupportsInt, TypeVar

from utility.system.path import Path

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from typing_extensions import Buffer, SupportsIndex


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
        return self._get("x86", "x64")

    def get_int(self):
        return self._get(32, 64)

    def get_dashed_bitness(self):
        return self._get("32-bit", "64-bit")

    # TODO Rename this here and in `get_machine_repr`, `get_int` and `get_dashed_bitness`
    def _get(self, arg0, arg1):  # sourcery skip: assign-if-exp, reintroduce-else
        if self == self.BIT_32:
            return arg0
        if self == self.BIT_64:
            return arg1
        return None

    def supports_64_bit(self) -> bool:
        """Check if the architecture supports 64-bit processing."""
        return self == self.BIT_64


def format_gpu_info(info, headers):
    # Determine the maximum width for each column
    column_widths: list[int] = [max(len(str(row[i])) for row in (headers, *info)) for i in range(len(headers))]

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
        gpu_info.extend(
            (
                gpu.id,
                gpu.name,
                f"{gpu.memoryTotal}MB",
                f"{gpu.memoryUsed}MB",
                f"{gpu.memoryFree}MB",
                f"{gpu.driver}",
                f"{gpu.temperature} C",
            )
            for gpu in gpus
        )
        info["GPU Details"] = format_gpu_info(gpu_info, headers=("id", "name", "total memory", "used memory", "free memory", "driver", "temperature"))

    return info

T = TypeVar("T")


def remove_duplicates(my_list: list[T], *, case_insensitive: bool = False) -> list[T]:
    seen = set()
    return [
        x.lower() if case_insensitive and isinstance(x, str) else x
        for x in my_list
        if not (x in seen or seen.add(x))
    ]


def is_debug_mode() -> bool:
    ret = False
    if os.getenv("PYTHONDEBUG", None):
        ret = True
    if os.getenv("DEBUG_MODE", "0") == "1":
        ret = True
    if getattr(sys, "gettrace", None) is not None:
        ret = True
    print(f"DEBUG MODE: {ret}")
    return ret


def has_attr_excluding_object(cls: type, attr_name: str) -> bool:
    # Exclude the built-in 'object' class
    mro_classes = [c for c in cls.mro() if c != object]

    return any(attr_name in base_class.__dict__ for base_class in mro_classes)


def is_class_or_subclass_but_not_instance(cls: type, target_cls: type) -> bool:
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(instance: object, target_cls: type) -> bool:
    if hasattr(instance, "__bases__"):  # instance is a class
        return False  # if instance is a class type, always return False
    # instance is not a class
    instance_type = instance.__class__
    return instance_type is target_cls or is_class_or_subclass_but_not_instance(instance_type, target_cls)


def generate_hash(
    data_input: bytes | bytearray | memoryview | os.PathLike | str,
    hash_algo: str = "sha1",  # sha1 is faster than md5 in python somehow
    chunk_size: int = 262144,  # 256KB default
    *,
    always_chunk: bool = False,  # Don't unnecessarily chunk bytes/bytearray inputs.
) -> str:
    # Create a hash object for the specified algorithm
    try:
        hasher = hashlib.new(hash_algo)
    except ValueError as e:
        available_algos = ", ".join(sorted(hashlib.algorithms_available))
        msg = f"Invalid hash algorithm. Available algorithms are: [{available_algos}]"
        raise ValueError(msg) from e

    if isinstance(data_input, (bytes, bytearray, memoryview)):
        # Process the byte-like data in chunks
        if always_chunk or isinstance(data_input, memoryview):
            for start in range(0, len(data_input), chunk_size):
                end = start + chunk_size
                hasher.update(data_input[start:end])
        else:
            hasher.update(data_input)
    else:
        with Path.pathify(data_input).open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)

    # Special handling for SHAKE algorithms which require a digest length
    if "shake" in hash_algo:
        # Producing a 64-byte (512 bits) output
        return hasher.hexdigest(64)  # type: ignore[]
    return hasher.hexdigest()


def indent(
    elem: Element,
    level: int = 0,
):
    """Indents the XML element by the given level
    Args:
        elem: Element - The element to indent
        level: int - The level of indentation (default: 0).

    Returns:
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


def is_int(val: str | int | Buffer | SupportsInt | SupportsIndex) -> bool:
    """Can be cast to an int without raising an error.

    Args:
    ----
        val (ConvertableToInt): The value to try to convert

    Returns:
    -------
        True if val can be converted else False
    """
    try:
        _ = int(val)
    except ValueError:
        return False
    else:
        return True


def is_float(val: str | float | Buffer | SupportsFloat | SupportsIndex) -> bool:
    """Can be cast to a float without raising an error.

    Args:
    ----
        val (ConvertableToFloat): The value to try to convert

    Returns:
    -------
        True if val can be converted else False
    """
    try:
        _ = float(val)
    except ValueError:
        return False
    else:
        return True
