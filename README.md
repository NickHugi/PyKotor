PyKotor
=======
A comprehensive and exhaustive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

## Installation
(The PyPI egg is currently in maintenance. Please check back later) Install from [PyPI](https://pypi.org/project/PyKotor/).
```commandline
pip install pykotor
```

## Requirements
PyKotor supports any Python version between 3.8 and 3.12. See requirements-dev.txt and pyproject.toml for additional pip dependencies.
PyKotor is supported on most (if not all) operating systems. Yes, this includes Mac and any other case-sensitive filesystem.

## Cloning the repo
If you would like to work with the source files directly from GitHub, run the following commands to get yourself set:
Note: Linux/Mac users need to instead execute `pwsh ./install_python_venv.ps1`.
```commandline
git clone https://github.com/NickHugi/PyKotor
cd PyKotor
./install_python_venv.ps1
```
If you are on Linux/Mac and do not have Powershell installed, simply run the command `/bin/bash ./install_powershell.sh` first, then try to run install_python_venv.ps1 again.

On windows, if you get the error:
```
install_python_venv.ps1 is not digitally signed. You cannot run this script on the current system.
```
you can bypass this error by running `PowerShell.exe -ExecutionPolicy Bypass -File .\compile_holopatcher.ps1`

Otherwise, see https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell?view=powershell-7.4 to learn how to install PowerShell on your system or install Python manually from https://www.python.org/, then set your environment variable PYTHONPATH manually by looking inside the '.env' file in the root of this repo.


Once 'install_python_venv.ps1' finishes, you can run any of the provided Tools, such as HoloPatcher, KotorDiff, or the Toolset, like this:
```commandline
pip install -r Tools/HoloPatcher/requirements.txt --prefer-binary
python ./Tools/HoloPatcher/src/__main__.py
pip install -r Tools/HolocronToolset/requirements.txt --prefer-binary
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/KotorDiff/__main__.py
```

Install requirements-dev.txt to get all pip packages in one shot:
```commandline
pip install -r requirements-dev.txt --prefer-binary
```
Note: Most tools on here will automatically create the PYTHONPATH paths needed, but this is a generosity that will not reliably continue through commits. Common errors like 'import not found <utility.Path>' or 'import not found <pykotor>' may result. Just run the powershell script ./install_python_venv.ps1 to automatically configure all of this. PRs are welcome to port this powershell code to e.g. bash or another pre-installed language.

## Compiling/Building Available Tools:
After cloning the repo, open any of the powershell scripts in the `compile` folder such as `compile_holopatcher.ps1` and `compile_toolset.ps1` with PowerShell. Doing so will start an automated process that results in a EXE being built/compiled to the PyKotor/dist folder. Specifically, those scripts will:
- Find a compatible Python interpreter, otherwise will install Python 3.8
- Setup the environment (the venv and PYTHONPATH)
- Install the tool's dependencies. This is any pip packages they require from requirements.txt and recommended.txt
- Install PyInstaller
- Compile to executable binary, as one file, to the dist folder in the root level of the repository.

The compiling scripts rely on Powershell being installed, on Unix you may not have this installed and you'll need to run `/bin/bash install_powershell.sh` first. See `Cloning the Repo` above for more information.


## Coding Example Usage:
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
