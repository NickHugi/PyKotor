from setuptools import setup, find_packages

setup(
    name="utility",
    version="1.0.0",
    description="Utility Library",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Add any dependencies here
    ],
)
from setuptools import setup, find_packages

setup(
    name="utility",
    version="1.0.0",
    description="Utility package",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "loggerplus>=0.1.3,<1",
    ],
)
