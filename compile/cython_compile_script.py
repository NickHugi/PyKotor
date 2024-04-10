from __future__ import annotations  # noqa: INP001

from distutils.core import setup
from pathlib import Path

from Cython.Build import cythonize


def find_py_files(root_dir: Path) -> list[str]:
    return [str(file) for file in root_dir.rglob("*") if file.suffix.lower() == ".py"]


def find_extra_files(root_dir: Path) -> list[str]:
    return [
        str(file) for file in root_dir.rglob("*")
        if (
            file.suffix.lower() in {".py", ".pyd", ".so"}
            and file.is_file()
            and "cython" not in file.name.lower()
        )
    ]


def compile_cython_files(py_files):
    setup(
        ext_modules=cythonize(
            py_files,
            show_all_warnings=True,
            exclude_failures=True,
            compiler_directives={"embedsignature": True},
            language_level=2,
            verbose=True,
        ),
        script_args=["build_ext", "--inplace"],
    )


if __name__ == "__main__":
    workspace_folder = Path.cwd()  # Gets the current working directory

    # Directories to search for Python files
    # libraries_dir = Path.joinpath(workspace_folder, "Libraries")
    # tools_dir = Path.joinpath(workspace_folder, "Tools")
    venv_dir = Path.joinpath(workspace_folder, ".venv")

    # Find all Python files
    # py_files: list[str] = find_py_files(libraries_dir) + find_py_files(tools_dir)
    other_files: list[str] = find_extra_files(venv_dir)

    # Compile Python files with Cython
    compile_cython_files(other_files)
