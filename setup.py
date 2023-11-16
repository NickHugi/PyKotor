from pathlib import Path

from setuptools import find_namespace_packages, setup

HERE = Path(__file__).parent

NAME = "PyKotor"
VERSION = "1.7.0"
AUTHOR = "Nicholas Hugi"
DESCRIPTION = "Read, modify and write files used by KotOR's game engine."
PACKAGES = find_namespace_packages(exclude=["tests", "docs", "scripts/k_batchpatcher"])
URL = "https://github.com/NickHugi/PyKotor"

README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()
TOOLSET_REQUIREMENTS = (HERE / "toolset" / "requirements.txt").read_text().splitlines()
REQUIREMENTS.extend(TOOLSET_REQUIREMENTS)

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    install_requires=REQUIREMENTS,
    long_description=README,
    packages=PACKAGES,
    url=URL,
    long_description_content_type="text/markdown",
)
