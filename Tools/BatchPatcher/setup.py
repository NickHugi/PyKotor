from setuptools import setup, find_packages

setup(
    name="batch-patcher",
    version="1.0.0",
    description="Batch Patcher",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "utility",
        # Add any other dependencies here
    ],
)
from setuptools import setup, find_packages

setup(
    name="batch-patcher",
    version="1.0.0",
    description="Batch Patcher",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "utility",
    ],
)
