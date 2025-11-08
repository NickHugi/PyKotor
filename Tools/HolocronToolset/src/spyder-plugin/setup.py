from __future__ import annotations

import os

from setuptools import find_packages, setup

# Get long description from README.md
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="spyder-holocron-toolset",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "spyder>=5.0.0",
        "qtpy",
        "pykotor",  # Add any other dependencies specific to your toolset
    ],
    entry_points={
        "spyder.plugins": [
            "spyder_holocron_toolset = spyder_holocron_toolset.spyder.plugin:HolocronToolset",
        ],
    },
    description="KotOR modding toolset for Spyder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    license="MIT",
    url="https://github.com/yourusername/spyder-holocron-toolset",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Spyder",
    ],
    package_data={
        "spyder_holocron_toolset": ["spyder/images/*"],
    },
)
