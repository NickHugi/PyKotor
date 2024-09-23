
PyKotor
=======
A comprehensive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/NickHugi/PyKotor
   cd PyKotor
   ```

2. Install Poetry (if not already installed):
   ```
   pip install poetry
   ```

3. Install the project and its dependencies:
   ```
   poetry install
   ```

4. Activate the virtual environment:
   ```
   poetry shell
   ```

This will install PyKotor and all its subpackages in editable mode.

## Requirements
PyKotor supports Python versions 3.8 and above. All dependencies are managed by Poetry.
PyKotor is supported on most (if not all) operating systems, including Mac and other case-sensitive filesystems.

## Running the tools

After installation and activating the virtual environment, you can run any of the provided tools, such as HoloPatcher, KotorDiff, or the Toolset, like this:

```
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/HoloPatcher/src/holopatcher/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

## Development

To install development dependencies, use:

```
poetry install --with dev
```

This will install all the development tools like mypy, ruff, pylint, etc.

## Running the tools

After installation, you can run any of the provided tools, such as HoloPatcher, KotorDiff, or the Toolset, like this:

```
python Tools/HoloPatcher/src/holopatcher/__main__.py
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

See [HoloPatcher's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HoloPatcher#readme) for more information

See [HolocronToolset's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HolocronToolset#readme) for more information

## Compiling/Building Available Tools:
After cloning the repo, open any of the powershell scripts in the `compile` folder such as `compile_holopatcher.ps1` and `compile_toolset.ps1` with PowerShell. Run the `deps_holopatcher.ps1` or `deps_toolset.ps1` first to get the dependencies setup. Doing so will start an automated process that results in a EXE being built/compiled to the PyKotor/dist folder. Specifically, those scripts will:
- Find a compatible Python interpreter, otherwise will install Python 3.8
- Setup the environment (the venv and PYTHONPATH)
- Install the tool's dependencies. This is any pip packages they require from requirements.txt and recommended.txt
- Install PyInstaller
- Compile to executable binary, as one file, to the dist folder in the root level of this repository.


## Working with Installation class in src:
Simple example of loading data from a game directory, searching for a specific texture, and exporting it to the TGA format.
```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, "./C_Gammorean01.tga", ResourceType.TGA)
```
As shown, this will save `C_Gammorean01.tga` to the current directory.
[More examples](https://github.com/NickHugi/PyKotor/blob/master/Libraries/PyKotor/docs/installation.md)

## Tests

These represent the currently passing/failing python versions/operating system combinations. Each badge is hyperlinked and permalinked to the full test report. Pick and choose any commit and see how far we have come.

### Windows:

<!-- WINDOWS-BADGES-START -->
[![python-3.7-x86-Build_Failed](https://img.shields.io/badge/python--3.7--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.8-x86-Build_Failed](https://img.shields.io/badge/python--3.8--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.8-x64-Build_Failed](https://img.shields.io/badge/python--3.8--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.9-x86-Build_Failed](https://img.shields.io/badge/python--3.9--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.9-x64-Build_Failed](https://img.shields.io/badge/python--3.9--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.10-x86-Build_Failed](https://img.shields.io/badge/python--3.10--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.10-x64-Build_Failed](https://img.shields.io/badge/python--3.10--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.11-x86-Build_Failed](https://img.shields.io/badge/python--3.11--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.11-x64-Build_Failed](https://img.shields.io/badge/python--3.11--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.12-x86-Build_Failed](https://img.shields.io/badge/python--3.12--x86_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.12-x64-Build_Failed](https://img.shields.io/badge/python--3.12--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
<!-- WINDOWS-BADGES-END -->

### Linux:

<!-- LINUX-BADGES-START -->
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.8-x64-Build_Failed](https://img.shields.io/badge/python--3.8--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.9-x64-Build_Failed](https://img.shields.io/badge/python--3.9--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.10-x64-Build_Failed](https://img.shields.io/badge/python--3.10--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.11-x64-Build_Failed](https://img.shields.io/badge/python--3.11--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.12-x64-Build_Failed](https://img.shields.io/badge/python--3.12--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
<!-- LINUX-BADGES-END -->

### MacOS:

<!-- MACOS-BADGES-START -->
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.8-x64-Build_Failed](https://img.shields.io/badge/python--3.8--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.9-x64-Build_Failed](https://img.shields.io/badge/python--3.9--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.10-x64-Build_Failed](https://img.shields.io/badge/python--3.10--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.11-x64-Build_Failed](https://img.shields.io/badge/python--3.11--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
[![python-3.12-x64-Build_Failed](https://img.shields.io/badge/python--3.12--x64_Build_Failed-lightgrey)](https://github.com/th3w1zard1/PyKotor/actions/runs/10988098582)
<!-- MACOS-BADGES-END -->

## License
This repository falls under the [LGPL-3.0-or-later License](https://github.com/NickHugi/PyKotor/blob/master/LICENSE).


































