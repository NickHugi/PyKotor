"""Setup script for PyKotorEngine.

A Panda3D-based game engine for Knights of the Old Republic.
"""

from setuptools import setup, find_packages

setup(
    name="pykotorengine",
    version="0.1.0",
    description="Panda3D-based game engine for Knights of the Old Republic",
    author="PyKotor Contributors",
    python_requires=">=3.11",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "panda3d>=1.10.13",
        # PyKotor is assumed to be installed separately from Libraries/PyKotor
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

