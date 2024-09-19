from setuptools import setup, find_packages

setup(
    name="pykotor-workspace",
    version="1.0.0",
    packages=find_packages(where="Libraries/PyKotor/src") +
             find_packages(where="Libraries/PyKotorFont/src") +
             find_packages(where="Libraries/PyKotorGL/src") +
             find_packages(where="Libraries/Utility/src") +
             find_packages(where="Tools/HolocronToolset/src") +
             find_packages(where="Tools/HoloPatcher/src") +
             find_packages(where="Tools/KotorDiff/src") +
             find_packages(where="Tools/BatchPatcher/src"),
    package_dir={
        "pykotor": "Libraries/PyKotor/src/pykotor",
        "pykotorfont": "Libraries/PyKotorFont/src/pykotor",
        "pykotorgl": "Libraries/PyKotorGL/src/pykotor",
        "utility": "Libraries/Utility/src/utility",
        "toolset": "Tools/HolocronToolset/src/toolset",
        "holopatcher": "Tools/HoloPatcher/src/holopatcher",
        "kotordiff": "Tools/KotorDiff/src/kotordiff",
        "batchpatcher": "Tools/BatchPatcher/src/batchpatcher",
    },
    install_requires=[
        "loggerplus>=0.1.3",
    ],
    extras_require={
        "tools": ["qasync>=0.23.0"],
        "dev": [
            "mypy",
            "ruff",
            "pylint",
            "snakeviz",
            "autoflake",
            "pytest",
            "pytest-xdist",
            "pytest-html",
            "types-Pillow",
            "types-Send2Trash",
            "send2trash",
            "black",
            "flake8",
        ],
    },
)
