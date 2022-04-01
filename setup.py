import pathlib

from setuptools import setup, find_namespace_packages

HERE = pathlib.Path(__file__).parent

NAME = "HolocronToolset"
VERSION = "2.0.0"
AUTHOR = "Nicholas Hugi"
DESCRIPTION = "A PyQt5 application that can edit the files used by the KotOR game engine."
PACKAGES = find_namespace_packages()
URL = "https://github.com/NickHugi/PyKotor"

README = (HERE / "README.rd").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text()

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    install_requires=REQUIREMENTS,
    long_description=README,
    packages=PACKAGES,
    url=URL
)