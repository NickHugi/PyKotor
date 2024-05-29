from __future__ import annotations

import importlib
import sys

from pathlib import Path
from typing import Any

from utility.logger_util import RobustRootLogger


def debug_reload_pymodules():  # sourcery skip: remove-unreachable-code
    """Reload all imported modules and log their names and file paths.

    Currently does not work, something about updating instances/classes implementation missing.
    """
    def is_builtin_module(module: Any) -> bool:
        """Check if the module is a built-in module."""
        return module.__name__ in sys.builtin_module_names

    def is_standard_library_module(module: Any) -> bool:
        """Check if the module is part of the standard library."""
        file_path: str | None = getattr(module, "__file__", None)
        if file_path is not None and file_path.strip():
            # Check if the module file path starts with the standard library path
            return file_path.startswith(sys.base_prefix) and "site-packages" not in file_path
        return False

    def is_site_packages_module(file_path_str: str) -> bool:
        lower_filepath = None if file_path is None else file_path_str.lower()
        return (
            not lower_filepath
            or "site-packages" in lower_filepath
            or "dist-packages" in lower_filepath
        )

    modules_to_reload = list(sys.modules.items())

    for name, loaded_module in modules_to_reload:
        if loaded_module is None:
            continue
        if is_builtin_module(loaded_module):
            continue
        if is_standard_library_module(loaded_module):
            continue
        if is_site_packages_module(loaded_module):
            continue
        file_path: str | None = getattr(loaded_module, "__file__", None)
        if not file_path or not file_path.strip():
            continue
        if name.startswith(("debugpy", "pydevd", "_pydevd", "_pydev", "pydev_ipython")):
            continue
        try:
            reloaded_module = importlib.reload(loaded_module)
            loaded_module.__dict__.update(reloaded_module.__dict__)
        except TypeError as e:
            RobustRootLogger.warning(f"TypeError: Cannot reload module: {name}, {e}")
        except NotImplementedError:
            RobustRootLogger.warning(f"Cannot reload built-in module: {name}, falling back to alternative method!!")
            # Fallback to manual reload
            try:
                with Path(file_path).open("r") as f:
                    exec(f.read(), loaded_module.__dict__)
                    RobustRootLogger.debug(f"Manually reloaded '{name}' from '{file_path}'.")
            except Exception as e:  # noqa: BLE001
                RobustRootLogger.exception(f"Failed to manually reload '{name}' from '{file_path}': {e}")
        except ModuleNotFoundError as e:
            RobustRootLogger.warning(f"ModuleNotFoundError: Cannot reload module: {name}, {e}")
        except ImportError as e:
            RobustRootLogger.warning(f"ImportError: Cannot reload module: {name}, {e}")
        except Exception as e:  # noqa: BLE001
            RobustRootLogger.exception(f"{e.__class__.__name__}: Failed to reload module {name}: {e}")
        else:
            RobustRootLogger.info(f"Successfully reloaded '{name}' from '{file_path}'")

    # Special handling for reloading the entry point module
    main_module = sys.modules.get("__main__")
    if main_module:
        main_module_file_path = getattr(main_module, "__file__", None)
        if main_module_file_path:
            try:
                # Save the current __name__ and set a temporary one
                original_name = main_module.__name__
                main_module.__name__ = "__main_reloaded__"

                spec = importlib.util.spec_from_file_location("__main_reloaded__", main_module_file_path)
                new_main_module = importlib.util.module_from_spec(spec)
                sys.modules["__main_reloaded__"] = new_main_module
                spec.loader.exec_module(new_main_module)

                # Restore the original __name__
                new_main_module.__name__ = original_name
                sys.modules["__main__"] = new_main_module
                del sys.modules["__main_reloaded__"]

                RobustRootLogger.info(f"Successfully reloaded entry point module '__main__' from '{main_module_file_path}'")
            except Exception as e:  # noqa: BLE001
                RobustRootLogger.exception(f"Failed to reload entry point module '__main__': {e}")
        else:
            RobustRootLogger.error(f"File path not found for main module {main_module}")
    else:
        RobustRootLogger.error("Main module not found?")
