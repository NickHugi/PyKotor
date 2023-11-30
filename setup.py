from setuptools import setup, find_packages

NAME = "PyKotor"
VERSION = 1.0
AUTHOR = "Nicholas Hugi"
DESCRIPTION = "Read, modify and write files used by KotOR's game engine."
PACKAGES = find_packages(exclude=['tests*'])

with open("requirements.txt", 'r') as file:
    REQUIREMENTS = file.read()

with open("README.rd", 'r') as file:
    README = file.read()

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    install_requires=REQUIREMENTS,
    long_description=README,
    packages=PACKAGES
)
