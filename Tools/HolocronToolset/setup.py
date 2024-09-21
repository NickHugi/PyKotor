from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="holocron-toolset",
    version="1.0.0",
    description="Holocron Toolset",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "utility",
        # Add any other dependencies here
    ],
)
from setuptools import find_packages, setup

setup(
    name="holocron-toolset",
    version="1.0.0",
    description="Holocron Toolset",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "pykotorfont",
        "pykotorgl",
        "utility",
        "qasync>=0.23.0,<0.24.0",
        "loggerplus>=0.1.3,<1",
    ],
)
