from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="pykotor",
    version="1.0.0",
    description="PyKotor Core Library",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Add any dependencies here
    ],
)
from setuptools import find_packages, setup

setup(
    name="pykotor",
    version="1.0.0",
    description="PyKotor core package",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ply>=3.11,<4",
        "loggerplus>=0.1.3,<1",
    ],
)
