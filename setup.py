import pathlib
from setuptools import setup, find_packages, find_namespace_packages

HERE = pathlib.Path(__file__).parent

NAME = "PyKotorGL"
VERSION = "1.2.2"
AUTHOR = "Nicholas Hugi"
DESCRIPTION = "Render modules from both KotOR games."
PACKAGES = find_namespace_packages()
URL = "https://github.com/NickHugi/PyKotorGL"

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
