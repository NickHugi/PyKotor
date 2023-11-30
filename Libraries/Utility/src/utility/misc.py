from __future__ import annotations

import hashlib
import os
import platform
import sys
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING

from utility.path import BasePath, Path

if TYPE_CHECKING:
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

def format_gpu_info(info, headers):
    # Determine the maximum width for each column
    column_widths = [max(len(str(row[i])) for row in [headers, *info]) for i in range(len(headers))]

    # Function to format a single row
    def format_row(row):
        return " | ".join(f"{str(item).ljust(column_widths[i])}" for i, item in enumerate(row))

    # Build the output string
    output = format_row(headers) + "\n"
    output += "-" * (sum(column_widths) + len(headers) * 3 - 1) + "\n"  # Add a separator line

    # Append each row of GPU details to the output string
    for row in info:
        output += format_row(row) + "\n"

    return output

def get_system_info():
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
    print(f"DEBUG MODE: {ret!s}")
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


def generate_filehash_sha256(filepath: os.PathLike | str) -> str:
    sha1_hash = hashlib.sha256()
    filepath = filepath if isinstance(filepath, BasePath) else Path(filepath)
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
