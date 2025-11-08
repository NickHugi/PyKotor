"""This is PyInstaller hook file for CEF Python. This file
helps PyInstaller find CEF Python dependencies that are
required to run the final executable.

See PyInstaller docs for hooks:
https://pyinstaller.readthedocs.io/en/stable/hooks.html
"""
#!/usr/bin/env python3
from __future__ import annotations

import glob
import logging
import os
import re
import sys

import PyInstaller

from PyInstaller.compat import is_darwin, is_linux, is_win
from PyInstaller.utils.hooks import collect_dynamic_libs, get_package_paths, is_module_satisfies

try:
    # PyInstaller >= 4.0 doesn't support Python 2.7
    from PyInstaller.compat import is_py2  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    is_py2 = None
    is_darwin = sys.platform == "darwin"
    is_linux = sys.platform.startswith("linux")
    is_win = sys.platform == "win32"

# Constants
CEFPYTHON_MIN_VERSION = "57.0"
PYINSTALLER_MIN_VERSION = "3.2.1"

# Get CEF Python package paths
CEFPYTHON3_DIR = get_package_paths("cefpython3")[1]

CYTHON_MODULE_EXT = ".pyd" if is_win else ".so"

# Globals
logger = logging.getLogger(__name__)

# Functions
def check_platforms():
    if not (is_win or is_darwin or is_linux):
        raise SystemExit("Error: Currently only Windows, Linux, and Darwin platforms are supported, see PyInstaller Issue #135.")

def check_pyinstaller_version():
    """Ensure PyInstaller version is supported."""
    result = re.search(r"^\d+\.\d+(\.\d+)?", PyInstaller.__version__)
    assert result is not None, str(result)
    version = result[0]
    if version < PYINSTALLER_MIN_VERSION:
        raise SystemExit(f"Error: pyinstaller {PYINSTALLER_MIN_VERSION} or higher is required")

def check_cefpython3_version():
    if not is_module_satisfies(f"cefpython3 >= {CEFPYTHON_MIN_VERSION}"):
        raise SystemExit(f"Error: cefpython3 {CEFPYTHON_MIN_VERSION} or higher is required")

def get_cefpython_modules() -> list[str]:
    """Get all cefpython Cython modules in the cefpython3 package."""
    pyds = glob.glob(os.path.join(CEFPYTHON3_DIR, f"cefpython_py*{CYTHON_MODULE_EXT}"))  # noqa: PTH118, PTH207
    assert len(pyds) > 1, "Missing cefpython3 Cython modules"
    modules = [os.path.basename(path).replace(CYTHON_MODULE_EXT, "") for path in pyds]  # noqa: PTH119
    return modules

def get_excluded_cefpython_modules() -> list[str]:
    """Get excluded cefpython modules not compatible with the current Python version."""
    pyver_string = f"py{''.join(map(str, sys.version_info[:2]))}"
    return [f"cefpython3.{mod}" for mod in get_cefpython_modules() if pyver_string not in mod]

def get_cefpython3_datas() -> list[tuple[str, str]]:  # noqa: C901
    """Collect data files required by cefpython3."""
    ret = []
    cefdatadir = "."

    # Binaries, licenses, and readmes in the cefpython3/ directory
    for filename in os.listdir(CEFPYTHON3_DIR):
        if filename[: -len(CYTHON_MODULE_EXT)] in get_cefpython_modules():
            continue

        extension = os.path.splitext(filename)[1]  # noqa: PTH122
        if extension in [".exe", ".dll", ".pak", ".dat", ".bin", ".txt", ".so", ".plist"] or filename.lower().startswith("license"):
            ret.append((os.path.join(CEFPYTHON3_DIR, filename), cefdatadir))  # noqa: PTH118
            logger.info(f"Include cefpython3 data: {filename}")

    # Collect additional data based on platform
    if is_darwin:
        resources_subdir = os.path.join("Chromium Embedded Framework.framework", "Resources")  # noqa: PTH118
        base_path = os.path.join(CEFPYTHON3_DIR, resources_subdir)  # noqa: PTH118
        assert os.path.exists(base_path), f"'{resources_subdir}' dir not found in cefpython3"  # noqa: PTH110
        for path, _, files in os.walk(base_path):
            for file in files:
                absolute_file_path = os.path.join(path, file)  # noqa: PTH118
                dest_path = os.path.relpath(path, CEFPYTHON3_DIR)
                ret.append((absolute_file_path, dest_path))
                logger.info(f"Include cefpython3 data: {dest_path}")
    elif is_win or is_linux:
        locales_dir = os.path.join(CEFPYTHON3_DIR, "locales")  # noqa: PTH118
        assert os.path.exists(locales_dir), "locales/ dir not found in cefpython3"  # noqa: PTH110
        for filename in os.listdir(locales_dir):
            ret.append((os.path.join(locales_dir, filename), os.path.join(cefdatadir, "locales")))  # noqa: PTH118
            logger.info(f"Include cefpython3 data: {os.path.basename(locales_dir)}/{filename}")  # noqa: PTH119

        swiftshader_dir = os.path.join(CEFPYTHON3_DIR, "swiftshader")  # noqa: PTH118
        if os.path.isdir(swiftshader_dir):  # noqa: PTH112
            for filename in os.listdir(swiftshader_dir):
                ret.append((os.path.join(swiftshader_dir, filename), os.path.join(cefdatadir, "swiftshader")))  # noqa: PTH118
                logger.info(f"Include cefpython3 data: {os.path.basename(swiftshader_dir)}/{filename}")  # noqa: PTH119

    return ret

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

# Checks
check_platforms()
check_pyinstaller_version()
check_cefpython3_version()

# Info
logger.info(f"CEF Python package directory: '{CEFPYTHON3_DIR}'")

# Hidden imports
hiddenimports = [
    "codecs", "copy", "datetime", "inspect", "json", "os", "platform",
    "random", "re", "sys", "time", "traceback", "types", "urllib", "weakref"
]
if is_py2:
    hiddenimports.append("urlparse")

# Excluded modules
excludedimports = get_excluded_cefpython_modules()

# Include binaries
if is_darwin or is_linux:
    binaries = [(os.path.join(CEFPYTHON3_DIR, "subprocess"), ".")]  # noqa: PTH118
elif is_win:
    binaries = [(os.path.join(CEFPYTHON3_DIR, "subprocess.exe"), ".")]  # noqa: PTH118
else:
    binaries = []

# Include dynamic libraries
binaries += collect_dynamic_libs("cefpython3")

# Include datas
datas = get_cefpython3_datas()

# Notify PyInstaller that this hook was executed
os.environ["PYINSTALLER_CEFPYTHON3_HOOK_SUCCEEDED"] = "1"
