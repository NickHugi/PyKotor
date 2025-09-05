from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="kotor-diff",
    version="1.0.0",
    description="KotOR Diff Tool",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
