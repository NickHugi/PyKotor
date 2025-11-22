from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="holopazaak",
    version="1.0.0",
    description="HoloPazaak - A PyQt5 Pazaak card game",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "qtpy>=2.4.3",
        "PyQt5>=5.15; python_implementation == 'CPython'",
        "PyQt5-Qt5>=5.15; python_implementation == 'CPython'",
        "PyQt5-sip>=12.10; python_implementation == 'CPython'",
        "PySide6>=6.0; python_implementation == 'PyPy'",
    ],
)

