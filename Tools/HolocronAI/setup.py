from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup

# Read requirements
requirements = [
    "numpy>=1.22.0",
    "sentence-transformers>=2.2.0",
    "typing-extensions>=4.0.0",
    "PyQt6>=6.4.0",
    "litellm>=1.0.0",
    "qtawesome>=1.2.0",  # For icons
    "darkdetect>=0.7.1",  # For auto dark/light theme
]

# Read README
readme = Path("README.md").read_text(encoding="utf-8") if Path("README.md").exists() else ""

setup(
    name="holocron-ai",
    version="0.1.0",
    description="Star Wars character AI chat interface using PyQt and LLMs",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="PyKotor Team",
    author_email="",
    url="https://github.com/NickHugi/PyKotor",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Games/Entertainment",
    ],
    entry_points={
        "console_scripts": [
            "holocron-ai=holocron_ai.gui:main",
        ],
    },
)
