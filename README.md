
PyKotor
=======

A comprehensive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Installation

### From PyPI

(The PyPI egg is currently in maintenance. Please check back later)  
Install from [PyPI](https://pypi.org/project/PyKotor/):

```commandline
pip install pykotor
```

### From source

1. Clone the repository:

   ```bash
   git clone https://github.com/NickHugi/PyKotor
   cd PyKotor
   ```

2. Install Poetry (if not already installed):

   ```bash
   pip install poetry
   ```

3. Install the project and its dependencies:

   ```bash
   poetry install
   ```

4. Activate the virtual environment:

   ```bash
   poetry shell
   ```

This will install PyKotor and all its subpackages in editable mode.

## Requirements

PyKotor supports Python versions 3.8 through 3.12 (and newer, e.g. 3.13).  
Dependencies are managed by Poetry or can be installed via `requirements-dev.txt` and `pyproject.toml`.  
PyKotor is supported on most operating systems, including Mac and other case‑sensitive filesystems.

## Running the tools

After installation and activating the virtual environment, you can run any of the provided tools, such as HoloPatcher, KotorDiff, or the Toolset:

```bash
python Tools/HoloPatcher/src/holopatcher/__main__.py
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

See [HoloPatcher's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HoloPatcher#readme) and  
[HolocronToolset's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HolocronToolset#readme) for more information.

Optionally, install all dev requirements in one shot:

```commandline
pip install -r requirements-dev.txt --prefer-binary
```

We use `--prefer-binary` as building pip packages from source can occasionally fail on some operating systems/python environments.

For more information on running our Powershell scripts, please see [POWERSHELL.md](https://github.com/NickHugi/PyKotor/blob/master/POWERSHELL.md).  
If Powershell is not an option, you can install Python manually from <https://www.python.org/> and set your environment variable `PYTHONPATH` manually by looking inside the `.env` file in the root of this repo.

## Development

To install development dependencies, use:

```bash
poetry install --with dev
```

This will install all the development tools like mypy, ruff, pylint, etc.

## Compiling/Building Available Tools

After cloning the repo, open any of the PowerShell scripts in the `compile` folder such as `compile_holopatcher.ps1` and `compile_toolset.ps1`.  
Run the `deps_holopatcher.ps1` or `deps_toolset.ps1` first to set up dependencies. Doing so will start an automated process that results in an EXE being built/compiled to the `PyKotor/dist` folder. Specifically, those scripts will:

- Find a compatible Python interpreter, otherwise install Python 3.8
- Set up the environment (venv and PYTHONPATH)
- Install the tool's dependencies from requirements files
- Install PyInstaller
- Compile to a single executable binary in the dist folder

## Working with Installation class in src

Simple example of loading data from a game directory, searching for a specific texture, and exporting it to the TGA format:

```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, "./C_Gammorean01.tga", ResourceType.TGA)
```

This saves `C_Gammorean01.tga` to the current directory.  
[More examples](https://github.com/NickHugi/PyKotor/blob/master/Libraries/PyKotor/docs/installation.md)

## License

This repository falls under the [LGPL-3.0-or-later License](https://github.com/NickHugi/PyKotor/blob/master/LICENSE).
