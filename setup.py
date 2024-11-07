from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="pykotor",
    version="0.1.0",
    description="PyKotor suite of packages",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="Libraries", include=["PyKotor.*", "Utility.*"]),
    package_dir={
        "": "Libraries"
    },
    install_requires=[
        "Utility",  # Assuming 'Utility' is the name of the utility package
    ],
    extras_require={
        "toolset": [
            "HolocronToolset",
            "HoloPatcher",
            "KotorDiff",
            "BatchPatcher",
        ],
    },
    entry_points={
        "console_scripts": [
            "holocron-toolset=Tools.HolocronToolset.src.main:main",
            "holopatcher=Tools.HoloPatcher.src.main:main",
            "kotordiff=Tools.KotorDiff.src.main:main",
            "batchpatcher=Tools.BatchPatcher.src.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
