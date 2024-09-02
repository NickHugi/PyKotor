#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

if sys.platform == "win32":
    exe_dir = os.path.dirname(sys.executable)
    dll_dir = exe_dir
    os.add_dll_directory(dll_dir)
elif sys.platform == "darwin":
    lib_dir = os.path.join(os.path.dirname(sys.executable), "cefpython3")
    os.environ["DYLD_LIBRARY_PATH"] = f"{lib_dir}:" + os.environ.get("DYLD_LIBRARY_PATH", "")

elif sys.platform.startswith("linux"):
    lib_dir = os.path.join(os.path.dirname(sys.executable), "cefpython3")
    os.environ["LD_LIBRARY_PATH"] = f"{lib_dir}:" + os.environ.get("LD_LIBRARY_PATH", "")
