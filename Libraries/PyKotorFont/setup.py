from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="pykotor-font",
    version="1.0.0",
    description="PyKotor Font Library",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        # Add any other dependencies here
    ],
)
from setuptools import find_packages, setup

setup(
    name="pykotorfont",
    version="1.0.0",
    description="PyKotor font package",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "Pillow>=9.5",
        "loggerplus>=0.1.3,<1",
    ],
)
