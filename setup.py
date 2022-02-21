import pathlib
from setuptools import setup, find_packages, find_namespace_packages

HERE = pathlib.Path(__file__).parent

NAME = "PyKotor"
VERSION = "0.21"
AUTHOR = "Nicholas Hugi"
DESCRIPTION = "Read, modify and write files used by KotOR's game engine."
PACKAGES = find_namespace_packages(exclude=["tests"])
URL = "https://github.com/NickHugi/PyKotor"

README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text()

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    install_requires=REQUIREMENTS,
    long_description=README,
    packages=PACKAGES,
    url=URL,
    long_description_content_type='text/markdown'
)
