PyKotor
=======
A comprehensive and exhaustive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Installation
(The PyPI egg is currently in maintenance. Please check back later) Install from [PyPI](https://pypi.org/project/PyKotor/).
```commandline
pip install pykotor
```

## Requirements
PyKotor supports any Python version within 3.8 through 3.12. See requirements.txt for additional pip dependencies.
PyKotor is supported on most (if not all) operating systems. Yes, this includes Mac and any other case-sensitive filesystem.

## Cloning the repo
If you would like to work with the source files directly from GitHub, run the following commands to get yourself set:
```commandline
git clone https://github.com/NickHugi/PyKotor
cd PyKotor
./install_python_venv.ps1
```
Note: if the command `./install_python_venv.ps1` fails with something like 'not found', you may need to instead run `pwsh ./install_python_venv.ps1`.
If you are on linux/mac and do not have powershell installed, simply run the command `/bin/bash ./install_powershell.sh` first, then try to run install_python_venv.ps1 again.
Once 'install_python_venv.ps1' finishes, you can run any of the provided Tools, such as HoloPatcher, KotorDiff or the Toolset, like this:
```commandline
python Tools/HoloPatcher/src/__main__.py  # Launch HoloPatcher
python Tools/HolocronToolset/src/toolset/__main__.py  # Launch Holocron Toolset
```

## Compiling/Building Available Tools:
After cloning the repo, open any of the powershell scripts in the `compile` folder such as `compile_holopatcher.ps1` and `compile_toolset.ps1` with powershell. Doing so will start an automated process that results in a EXE being built/compiled to the PyKotor/dist folder. Specifically, those scripts will:
- Install Python 3.8 (only if another compatible Python version is not already installed)
- Setup the environment (PYTHONPATH)
- Create a virtual environment
- Install the tool's dependencies. This is any pip packages they require from requirements.txt
- Install PyInstaller
- Compile to executable binary, as one file, to the PyKotor/dist folder.

## Coding Example Usage:
Simple example of loading data from a game directory, searching for a specific texture and exporting it to the TGA format.
```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, "./C_Gammorean01.tga", ResourceType.TGA)
```
As shown, this will save `C_Gammorean01.tga` to the current directory.

## Accessing the GUI Designer

Run the command from your terminal:

```commandline
pip install qt5-applications
```

You will then need to navigate to your Python's site-packages folder. You can determine its location through your terminal
with the following commands:

```commandline
python -m site --user-site
```

Then navigate to ```./qt5_applications/Qt/bin``` and open the ```designer.exe``` file.

## License
This repository falls under the [MIT License](https://github.com/NickHugi/PyKotor/blob/master/README.md).
