from setuptools import setup, find_packages

setup(
    name="pykotor-gl",
    version="1.0.0",
    description="PyKotor GL Library",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        # Add any other dependencies here
    ],
)
from setuptools import setup, find_packages

setup(
    name="pykotorgl",
    version="1.0.0",
    description="PyKotor GL package",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pykotor",
        "numpy~=1.22",
        "PyOpenGL~=3.1",
        "PyGLM>=2.0,<2.8",
        "loggerplus>=0.1.3,<1",
    ],
)
