from __future__ import annotations

from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
    cython_available = True
except ImportError:
    cython_available = False

ext_modules = []
if cython_available:
    ext_modules = cythonize([Extension("utility.system.path", ["utility/system/path.pyx"])])

setup(
    ext_modules=cythonize("path.pyx", annotate=True, compiler_directives={"language_level": "3"})
)
