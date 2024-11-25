#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import logging
import os
import platform
import stat
import sys

from collections import OrderedDict
from contextlib import suppress
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, SupportsFloat, SupportsInt, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable
    from xml.etree.ElementTree import Element

    from typing_extensions import Buffer, Literal, Self, SupportsIndex

T = TypeVar("T")
U = TypeVar("U")


class ProcessorArchitecture(Enum):
    BIT_32 = "32bit"
    BIT_64 = "64bit"

    def __str__(self) -> Literal["32bit", "64bit"]:
        return self.value

    def __int__(self) -> Literal[32, 64]:
        return self.get_int()

    @classmethod
    def from_os(cls) -> Self:
        return cls(platform.architecture()[0])

    @classmethod
    def from_python(cls) -> Literal[ProcessorArchitecture.BIT_64, ProcessorArchitecture.BIT_32]:
        return cls.BIT_64 if sys.maxsize > 2**32 else cls.BIT_32

    def get_machine_repr(self):
        return self._get("x86", "x64")

    def get_int(self) -> Literal[32, 64]:
        return self._get(32, 64)

    def get_dashed_bitness(self):
        return self._get("32-bit", "64-bit")

    def _get(self, arg0: T, arg1: U) -> T | U:  # sourcery skip: assign-if-exp, reintroduce-else  # noqa: ANN001
        if self == self.BIT_32:
            return arg0
        if self == self.BIT_64:
            return arg1
        raise RuntimeError(arg0, arg1)

    def supports_64_bit(self) -> bool:
        """Check if the architecture supports 64-bit processing."""
        return self == self.BIT_64


def format_gpu_info(
    info: Iterable,
    headers: tuple[str, ...],
) -> str:
    # Determine the maximum width for each column
    column_widths: list[int] = [max(len(str(row[i])) for row in (headers, *info)) for i in range(len(headers))]

    # Function to format a single row
    def format_row(row: Iterable) -> str:
        return " | ".join(f"{str(item).ljust(column_widths[i])}" for i, item in enumerate(row))

    # Build the output string
    output: str = format_row(headers) + "\n"
    output += "-" * (sum(column_widths) + len(headers) * 3 - 1) + "\n"  # Add a separator line

    # Append each row of GPU details to the output string
    for row in info:
        output += format_row(row) + "\n"

    return output


def print_excluding_base_classes(
    obj: object,
    exclude_base_classes: list[type[object]] | None = None,
):
    if exclude_base_classes is None:
        exclude_base_classes = [object, type]

    def get_base_class_attributes(base_classes: Iterable[type[object]]) -> set[str]:
        attrs = set()
        for base_class in base_classes:
            attrs.update(dir(base_class))
        return attrs

    def print_filtered_attributes(obj: object, obj_name: str, exclude_attrs: Iterable[str]):
        print(f"{obj_name} Attributes:")
        for attr in dir(obj):
            if not attr.startswith("_") and not callable(getattr(obj, attr)) and attr not in exclude_attrs:
                try:
                    print(f"  {attr}: {getattr(obj, attr)}")
                except Exception as ex:  # noqa: BLE001
                    print(f"  {attr}: Unable to retrieve value ({ex})")

    # Get the attributes of the base classes to exclude
    base_class_attrs = get_base_class_attributes(exclude_base_classes)

    # Print the filtered attributes of the object
    print_filtered_attributes(obj, obj.__class__.__name__, base_class_attrs)


def get_system_info() -> dict[str, Any]:
    # sourcery skip: extract-method, list-comprehension, merge-dict-assign
    info: dict[str, Any] = {}

    # Basic OS information
    info["Platform"] = platform.system()
    info["Platform-Release"] = platform.release()
    info["Platform-Version"] = platform.version()
    info["Architecture"] = platform.machine()

    # CPU information
    psutil = None
    with suppress(ImportError):
        import psutil  # pyright: ignore[reportMissingImports]  # type: ignore[no-redef]
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
        import GPUtil  # pyright: ignore[reportMissingImports]  # type: ignore[no-redef]
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


def is_debug_mode() -> bool:
    ret = False
    if os.getenv("PYTHONDEBUG", None):
        ret = True
    if getattr(sys, "gettrace", None) is not None:
        ret = True
    if getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", False):
        ret = False
    if os.getenv("DEBUG_MODE", "0") == "1":
        ret = True
    return ret


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False) or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable
    )


def has_attr_excluding_object(
    cls: type,
    attr_name: str,
) -> bool:
    # Exclude the built-in 'object' class
    mro_classes: list[type] = [c for c in cls.mro() if c is not object]

    return any(attr_name in base_class.__dict__ for base_class in mro_classes)


def is_class_or_subclass_but_not_instance(
    cls: type,
    target_cls: type,
) -> bool:
    if cls is target_cls:
        return True
    if not hasattr(cls, "__bases__"):
        return False
    return any(is_class_or_subclass_but_not_instance(base, target_cls) for base in cls.__bases__)


def is_instance_or_subinstance(
    instance: object,
    target_cls: type,
) -> bool:
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
    try:
        hasher = hashlib.new(hash_algo)
    except ValueError as e:
        available_algos = ", ".join(sorted(hashlib.algorithms_available))
        msg = f"Invalid hash algorithm. Available algorithms are: [{available_algos}]"
        raise ValueError(msg) from e

    if isinstance(data_input, (bytes, bytearray, memoryview)):
        if always_chunk or isinstance(data_input, memoryview):
            for start in range(0, len(data_input), chunk_size):
                end = start + chunk_size
                hasher.update(data_input[start:end])
        else:
            hasher.update(data_input)
    else:
        with Path(data_input).open("rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)

    return hasher.hexdigest(64) if "shake" in hash_algo else hasher.hexdigest()  # type: ignore[call-arg]


def get_file_attributes(
    path: Path,
) -> dict[str, bool]:
    attributes: dict[str, bool] = {
        "is_hidden": False,
        "is_system": False,
        "is_archive": False,
        "is_compressed": False,
        "is_encrypted": False,
        "is_readonly": False,
        "is_temporary": False,
    }

    # Check if file is hidden
    attributes["is_hidden"] = path.name.startswith(".") or bool(path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) if hasattr(stat, "FILE_ATTRIBUTE_HIDDEN") else False

    # Check if file is read-only
    attributes["is_readonly"] = not os.access(path, os.W_OK)

    # Check if file is temporary (based on name)
    attributes["is_temporary"] = path.name.endswith(".tmp")

    # Platform-specific checks
    if os.name == "nt":  # Windows
        try:
            import ctypes

            FILE_ATTRIBUTE_SYSTEM = 0x4
            FILE_ATTRIBUTE_ARCHIVE = 0x20
            FILE_ATTRIBUTE_COMPRESSED = 0x800
            FILE_ATTRIBUTE_ENCRYPTED = 0x4000

            attrs: int = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:
                attributes["is_system"] = bool(attrs & FILE_ATTRIBUTE_SYSTEM)
                attributes["is_archive"] = bool(attrs & FILE_ATTRIBUTE_ARCHIVE)
                attributes["is_compressed"] = bool(attrs & FILE_ATTRIBUTE_COMPRESSED)
                attributes["is_encrypted"] = bool(attrs & FILE_ATTRIBUTE_ENCRYPTED)
        except Exception:
            logging.getLogger(__name__).exception(f"Failed to get file attributes for: '{path}'")
    else:  # Unix-like systems
        # Check if file is system (based on location)
        attributes["is_system"] = str(path).startswith(("/etc", "/var", "/bin", "/sbin", "/usr/bin", "/usr/sbin"))

        # Check if file is archived (based on extension)
        archive_extensions = {".tar", ".gz", ".bz2", ".xz", ".zip", ".7z", ".rar"}
        attributes["is_archive"] = path.suffix.lower() in archive_extensions

        # Check if file is compressed (based on extension)
        compressed_extensions = {".gz", ".bz2", ".xz", ".zip", ".7z", ".rar"}
        attributes["is_compressed"] = path.suffix.lower() in compressed_extensions

        # Check if file is encrypted (based on extension, not reliable)
        encrypted_extensions = {".gpg", ".enc", ".asc"}
        attributes["is_encrypted"] = path.suffix.lower() in encrypted_extensions

    return attributes


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


def is_int(
    val: str | int | Buffer | SupportsInt | SupportsIndex,
) -> bool:
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


def is_float(
    val: str | float | Buffer | SupportsFloat | SupportsIndex,
) -> bool:
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


def to_kwargs(
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    if sys.version_info < (3, 7):  # noqa: UP036
        kwargs = OrderedDict(kwargs)
    keys = iter(kwargs.keys())
    for arg in args:
        try:
            key = next(keys)
            if kwargs[key] is None:
                kwargs[key] = arg
        except StopIteration as e:  # noqa: PERF203
            raise ValueError("Too many positional arguments for the available keyword arguments.") from e  # noqa: B904
    return dict(kwargs)
