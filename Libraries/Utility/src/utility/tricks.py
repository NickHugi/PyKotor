from __future__ import annotations

import contextlib
import ctypes
import gc
import importlib
import os
import platform
import sys
import time

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from types import ModuleType

BUILTIN_TYPES = (TypeVar, type, object, int, float, str, list, dict, set, tuple, frozenset, bool, bytes, complex, range, slice, type(Ellipsis), type(None))
BUILTIN_IDS = tuple(id(t) for t in BUILTIN_TYPES)
SENTINEL = object()


# Safe utility functions
def safe_type_getattr(
    obj: object,
    name: str,
) -> Any | object:
    try:
        return type.__getattribute__(obj, name)
    except (AttributeError, TypeError):
        return SENTINEL


def safe_object_getattr(
    cls: type,
    name: str,
) -> Any | object:
    try:
        return object.__getattribute__(cls, name)
    except (AttributeError, TypeError):
        return SENTINEL


def safe_type_setattr(
    cls: Any,
    name: str,
    value: Any,
):
    with contextlib.suppress(AttributeError, TypeError):
        type.__setattr__(cls, name, value)


def safe_object_setattr(
    obj: Any,
    name: str,
    value: Any,
):
    with contextlib.suppress(AttributeError, TypeError):
        object.__setattr__(obj, name, value)


def fallback_unknown_getattr(
    unk: Any,
    name: str,
) -> Any | object:
    test1 = safe_object_getattr(unk, name)
    if test1 is not SENTINEL:
        return test1
    test2 = safe_type_getattr(unk, name)
    if test2 is not SENTINEL:
        return test2
    try:
        test3 = getattr(unk, name, SENTINEL)
    except Exception:  # noqa: BLE001
        return SENTINEL
    else:
        return test3


def fallback_unknown_getmro(unk: Any) -> tuple[type, ...] | object:
    obj_cls = fallback_unknown_getattr(unk, "__class__")
    return fallback_unknown_getattr(obj_cls, "__mro__") if obj_cls is SENTINEL else obj_cls


def safe_isinstance(
    obj: Any,
    cls: type,
) -> bool | object:  # sourcery skip: assign-if-exp, reintroduce-else
    assert isinstance(cls, type)
    obj_cls_mro: tuple[type, ...] | object = fallback_unknown_getmro(obj)
    try:
        return cls in obj_cls_mro
    except Exception:  # noqa: BLE001
        return SENTINEL


def safe_dir(obj_or_cls: Any) -> list[str]:  # sourcery skip: assign-if-exp, reintroduce-else
    obj_or_cls_dict: dict[str, Any] | object = fallback_unknown_getattr(obj_or_cls, "__dict__")
    if obj_or_cls_dict is SENTINEL:
        return []
    return list(obj_or_cls_dict.keys())


def inherits_type_or_object(obj: object | type) -> bool | object:
    """Determine if an object inherits from type or object without invoking custom methods."""
    cls_mro: tuple[type, ...] | object = fallback_unknown_getmro(obj)
    with contextlib.suppress(Exception):
        return type in cls_mro or object in cls_mro
    return SENTINEL


def is_heap_type(cls: Any) -> bool | None:
    """Check if a class is a heap type."""
    Py_TPFLAGS_HEAPTYPE: int = 1 << 9  # Define the heap type flag
    flags: int | Any = safe_object_getattr(cls, "__flags__")
    return None if flags is SENTINEL else bool(flags & Py_TPFLAGS_HEAPTYPE)


def get_app_start_time() -> float:
    """Get the start time of the Python interpreter."""
    if platform.system() == "Windows":
        return win_get_interpreter_start_time()
    # On Unix-based systems, read /proc/self/stat for process start time
    with open("/proc/self/stat", errors="replace") as f:  # noqa: PTH123
        fields: list[str] = f.read().split()
        start_time_ticks: int = int(fields[21])
        clock_ticks_per_second: int = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
        start_time: float = start_time_ticks / clock_ticks_per_second
        return time.time() - (time.time() - start_time)


def win_get_interpreter_start_time() -> float:
    """Get the start time of the Python interpreter on Windows.

    This function uses the GetProcessTimes function from the Windows API to retrieve the process creation time.
    The FILETIME structure is used, which contains the creation time in 100-nanosecond intervals since January 1, 1601 (UTC).
    The conversion involves combining the FILETIME parts into a 64-bit value, converting to seconds, and adjusting to the Unix epoch.

    Returns:
    -------
        float: The start time of the interpreter as a Unix timestamp.
    """
    from ctypes.wintypes import DWORD, FILETIME, HANDLE

    # Load the kernel32 DLL
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    # Define required functions from kernel32
    GetCurrentProcess = kernel32.GetCurrentProcess
    GetCurrentProcess.restype = HANDLE
    GetProcessTimes = kernel32.GetProcessTimes
    GetProcessTimes.argtypes = [
        HANDLE,
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
        ctypes.POINTER(FILETIME),
    ]
    GetProcessTimes.restype = DWORD

    # Get the current process handle
    process: ctypes._NamedFuncPointer = GetCurrentProcess()

    # Initialize FILETIME structures to receive process times
    creation_time = FILETIME()
    exit_time = FILETIME()
    kernel_time = FILETIME()
    user_time = FILETIME()

    # Retrieve the process times
    if not GetProcessTimes(
        process,
        ctypes.byref(creation_time),
        ctypes.byref(exit_time),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time),
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    # Combine the low and high parts of the FILETIME structure to get the creation time in 100-nanosecond intervals
    creation_time_100ns: int = creation_time.dwLowDateTime + (creation_time.dwHighDateTime << 32)

    # Convert to seconds by dividing by 10,000,000 (100-nanosecond intervals per second)
    creation_time_seconds: float = creation_time_100ns / 1e7

    # Convert from FILETIME epoch (January 1, 1601) to Unix epoch (January 1, 1970)
    unix_epoch_offset = 11644473600  # Seconds between FILETIME epoch and Unix epoch
    creation_time_unix: float = creation_time_seconds - unix_epoch_offset

    return creation_time_unix


def is_builtin_class_instance(obj: object) -> bool:
    """Check if the object is an instance of a built-in class."""
    return obj.__class__.__module__ in ("builtins", "__builtin__") or obj.__class__.__name__ == "builtin_function_or_method"


def is_builtin_module(module: ModuleType) -> bool:
    """Check if the module is a built-in module."""
    return module.__name__ in sys.builtin_module_names


def is_standard_library_module(module: ModuleType) -> bool:
    """Check if the module is part of the standard library."""
    file_path: str | None = getattr(module, "__file__", None)
    if file_path is not None and file_path.strip():
        # Check if the module file path starts with the standard library path
        return file_path.startswith(sys.base_prefix) and "site-packages" not in file_path.lower()
    return False


def is_site_packages_module(file_path_str: str) -> bool:
    lower_filepath = file_path_str.lower()
    return "site-packages" in lower_filepath or "dist-packages" in lower_filepath


def reimport_dependencies(
    reloaded_module: ModuleType,
    importing_module: ModuleType,
):
    for name, value in vars(reloaded_module).items():
        if name in importing_module.__dict__:
            importing_module.__dict__[name] = value


def find_importing_modules(
    target_module_name: str,
) -> list[ModuleType]:
    importing_modules: list[ModuleType] = [name for name, module in sys.modules.items() if module and hasattr(module, "__file__") and target_module_name in sys.modules and target_module_name in module.__dict__.values()]
    return importing_modules


def debug_reload_pymodules():
    """Reload all imported modules that have changed on disk and log their names and file paths."""
    app_start_time: float = get_app_start_time()

    def get_last_modified_time(file_path: str) -> float:
        mtime = os.path.getmtime(file_path)  # noqa: PTH204
        return mtime

    def update_class_instances(
        old_module: ModuleType,
        new_module: ModuleType,
    ):
        """Update instances of classes from the old module to use the new class definitions from the reloaded module."""
        # Mapping from old classes to new classes
        class_map: dict[int, type] = {}

        # Populate the class mapping using id() to avoid unhashable issues
        for attr_name in safe_dir(old_module):
            try:
                old_class = safe_object_getattr(old_module, attr_name)
                if safe_isinstance(old_class, type):
                    new_class = safe_object_getattr(new_module, attr_name)
                    if safe_isinstance(new_class, type):
                        class_map[id(old_class)] = new_class
            except AttributeError:  # noqa: S112, PERF203
                continue

        # Function to update an object's class
        def update_object_class(obj, new_class):
            try:
                obj_cls = safe_object_getattr(obj, "__class__")
                # Update the class
                try:
                    object.__setattr__(obj, "__class__", new_class)
                except TypeError:
                    type.__setattr__(obj, "__class__", new_class)
                # if obj_cls.__name__ not in {"TypeVar", "PurePathType"}:
                #    print(f"Reloaded class '{new_class.__name__}'")
            except TypeError as e:
                ...  # print(f"Failed to update instance of type '{obj_cls.__name__}': {e}", file=sys.__stderr__)
            except Exception as e:  # noqa: BLE001
                print(f"Unexpected error occurred while updating instance of {obj_cls.__name__}: {e}", file=sys.__stderr__)

        # Track visited objects to avoid infinite recursion
        visited = set()

        # Update instances directly found by gc.get_objects()
        for obj in gc.get_objects():
            if id(obj) in BUILTIN_IDS:
                continue
            if is_builtin_class_instance(obj):
                continue
            try:
                obj_cls = safe_object_getattr(obj, "__class__")
                if id(obj_cls) in class_map:
                    new_class = class_map[id(obj_cls)]
                    update_object_class(obj, new_class)
                if id(obj) in class_map:
                    new_class = class_map[id(obj)]
                    update_object_class(obj, new_class)
            except Exception as e:  # noqa: PERF203, BLE001
                print(f"Error updating object {obj}: {e}", file=sys.__stderr__)

        # Recursively update referents
        def update_referents(obj):
            obj_id = id(obj)
            if obj_id in visited:
                return
            visited.add(obj_id)
            try:
                referents = gc.get_referents(obj)
                for ref in referents:
                    try:
                        ref_cls = safe_object_getattr(ref, "__class__")
                        if id(ref_cls) in class_map:
                            new_class = class_map[id(ref_cls)]
                            update_object_class(ref, new_class)
                        update_referents(ref)
                    except Exception as e:  # noqa: PERF203, BLE001
                        print(f"Error updating referent {ref} for object of type '{obj.__class__.__name__}': {e}", file=sys.__stderr__)
            except Exception as e:  # noqa: PERF203, BLE001
                print(f"Error getting referents for object of type '{obj.__class__.__name__}': {e}", file=sys.__stderr__)

        # Start the recursive update from all objects
        for obj in gc.get_objects():
            if id(obj) in BUILTIN_IDS:
                continue
            if is_builtin_class_instance(obj):
                continue
            # try:
            #    update_referents(obj)
            # except Exception as e:  # noqa: PERF203, BLE001
            #    print(f"Error updating referents for object of type '{obj.__class__.__name__}'): {e}", file=sys.__stderr__)

    def quick_update_class_instances(  # noqa: C901
        old_module: ModuleType,
        new_module: ModuleType,
    ):
        old_classes: dict[str, type] = {}
        new_classes: dict[str, type] = {}
        for name in dir(old_module):
            old_cls: type | object = fallback_unknown_getattr(old_module, name)
            if not isinstance(old_cls, type):
                continue
        for name in dir(new_module):
            new_cls: type | object = fallback_unknown_getattr(new_module, name)
            if safe_isinstance(new_cls, type):
                continue
        for obj in gc.get_objects():
            for name, old_class in old_classes.items():
                new_class: type | None = new_classes.get(name)
                if new_class:
                    if safe_isinstance(obj, old_class):
                        obj.__class__ = new_class
                    obj_dict: dict[str, Any] | object = fallback_unknown_getattr(obj, "__dict__")
                    if obj_dict is not SENTINEL and isinstance(obj_dict, dict):
                        for attr_name, old_cls in obj_dict.items():
                            if old_cls is old_class:
                                setattr(obj, attr_name, new_class)

    modules_to_reload: dict[str, ModuleType] = sys.modules.copy()
    for name, loaded_module in modules_to_reload.items():
        if loaded_module is None:
            continue
        if is_builtin_module(loaded_module):
            continue
        if is_standard_library_module(loaded_module):
            continue
        file_path: str | None = getattr(loaded_module, "__file__", None)
        if not file_path or not file_path.strip():
            continue
        if is_site_packages_module(file_path):
            continue
        if name.startswith(("pydevconsole", "debugpy", "pydevd", "_pydevd", "_pydev", "pydev_ipython", "__main__", "__mp_main__")):
            continue
        try:
            # Check if the module has changed on disk
            last_file_modified_time = get_last_modified_time(file_path)
            current_mtime = fallback_unknown_getattr(loaded_module, "__mtime__")
            if current_mtime is SENTINEL:
                current_mtime = app_start_time
                safe_object_setattr(loaded_module, "__mtime__", last_file_modified_time)
            if isinstance(last_file_modified_time, float) and isinstance(current_mtime, float) and last_file_modified_time <= current_mtime:
                continue  # No changes on disk, skip reloading
            logic_to_use = 0
            if logic_to_use < 1:
                reloaded_module = importlib.reload(loaded_module)
                safe_object_setattr(reloaded_module, "__mtime__", last_file_modified_time)
                if reloaded_module is not None:
                    importing_modules = find_importing_modules(name)
                    for importing_module_name in importing_modules:
                        importing_module = sys.modules[importing_module_name]
                        reimport_dependencies(reloaded_module, importing_module)
                        loaded_module.__dict__.update(reloaded_module.__dict__)
                if logic_to_use == -1:
                    update_class_instances(loaded_module, reloaded_module)
                else:
                    for attribute_name in dir(loaded_module):
                        old_attribute = getattr(loaded_module, attribute_name)
                        if isinstance(old_attribute, type) and old_attribute not in BUILTIN_TYPES:  # check if it's a class and not a builtin type
                            new_attribute = getattr(reloaded_module, attribute_name)
                            quick_update_class_instances(old_attribute, new_attribute)
            else:
                reloaded_module = importlib.reload(loaded_module)
                safe_object_setattr(reloaded_module, "__mtime__", last_file_modified_time)
                for attribute_name in dir(loaded_module):
                    old_attribute = getattr(loaded_module, attribute_name)
                    if isinstance(old_attribute, type) and old_attribute not in BUILTIN_TYPES:  # check if it's a class and not a builtin type
                        new_attribute = getattr(reloaded_module, attribute_name)
                        quick_update_class_instances(old_attribute, new_attribute)
            sys.modules[name] = reloaded_module
        except TypeError as e:
            ...
        except NotImplementedError:
            RobustLogger().warning(f"Cannot reload built-in module: {name}, falling back to alternative method!!")
            # Fallback to manual reload
            try:
                with Path(file_path).open("r") as f:
                    exec(f.read(), loaded_module.__dict__)
                    RobustLogger.debug(f"Manually reloaded '{name}' from '{file_path}'.")
            except Exception as e:  # noqa: BLE001
                RobustLogger().exception(f"Failed to manually reload '{name}' from '{file_path}': {e}")
        except ModuleNotFoundError as e:
            RobustLogger().warning(f"ModuleNotFoundError: Cannot reload module: {name}, {e}")
        except ImportError as e:
            RobustLogger().warning(f"ImportError: Cannot reload module: {name}, {e}")
        except Exception as e:  # noqa: BLE001
            RobustLogger().exception(f"{e.__class__.__name__}: Failed to reload module {name}: {e}")
        else:
            RobustLogger().info(f"Successfully reloaded '{name}' from '{file_path}'")
    RobustLogger().info("Reloading of python modules from their filepaths is complete.")

    # Special handling for reloading the entry point module
    return  # I don't think this works.
    main_module = sys.modules.get("__main__")
    if main_module:
        main_module_file_path = getattr(main_module, "__file__", None)
        if main_module_file_path:
            try:
                # Check if the main module has changed on disk
                last_file_modified_time = get_last_modified_time(main_module_file_path)
                last_mtime = getattr(main_module, "__mtime__", None)
                if last_mtime is not None and last_file_modified_time <= last_mtime:
                    return  # No changes on disk, skip reloading

                # Save the current __name__ and set a temporary one
                original_name = main_module.__name__
                main_module.__name__ = "__main_reloaded__"

                spec = importlib.util.spec_from_file_location("__main_reloaded__", main_module_file_path)
                new_main_module = importlib.util.module_from_spec(spec)
                sys.modules["__main_reloaded__"] = new_main_module
                spec.loader.exec_module(new_main_module)

                # Restore the original __name__
                new_main_module.__name__ = original_name
                new_main_module.__mtime__ = last_file_modified_time  # Update the modification time
                sys.modules["__main__"] = new_main_module
                del sys.modules["__main_reloaded__"]

                RobustLogger().info(f"Successfully reloaded entry point module '__main__' from '{main_module_file_path}'")
            except Exception as e:  # noqa: BLE001
                RobustLogger().exception(f"Failed to reload entry point module '__main__': {e}")
        else:
            RobustLogger().error(f"File path not found for main module {main_module}")
    else:
        RobustLogger().error("Main module not found?")
