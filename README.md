
PyKotor
=======
A comprehensive Python library that can read and modify most file formats used by the game [Knights of the Old Republic](https://en.wikipedia.org/wiki/Star_Wars:_Knights_of_the_Old_Republic_(video_game)) and its [sequel](https://en.wikipedia.org/wiki/Star_Wars_Knights_of_the_Old_Republic_II:_The_Sith_Lords).

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

**Note**: Linux/Mac users should initialize a powershell shell with the command `pwsh`, before executing the below commands:

```commandline
git clone https://github.com/NickHugi/PyKotor
cd PyKotor
./install_python_venv.ps1
```
For more information on running our Powershell scripts, please see [POWERSHELL.md](https://github.com/NickHugi/PyKotor/blob/master/POWERSHELL.md)

If powershell is not an option for you, you can install Python manually from https://www.python.org/, and set your environment variable PYTHONPATH manually by looking inside the '.env' file in the root of this repo.


Once 'install_python_venv.ps1' finishes, you can run any of the provided tools, such as HoloPatcher, KotorDiff, or the Toolset, like this:
```commandline
pip install -r Tools/HoloPatcher/requirements.txt --prefer-binary
python Tools/HoloPatcher/src/holopatcher/__main__.py
pip install -r Tools/HolocronToolset/requirements.txt --prefer-binary
python Tools/HolocronToolset/src/toolset/__main__.py
python Tools/KotorDiff/src/kotordiff/__main__.py
```

see [HoloPatcher's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HoloPatcher#readme) for more information

see [HolocronToolset's readme](https://github.com/NickHugi/PyKotor/tree/master/Tools/HolocronToolset#readme) for more information

Optionally, install requirements-dev.txt to get all pip packages in one shot:
```commandline
pip install -r requirements-dev.txt --prefer-binary
```
We use `--prefer-binary` as building pip packages from source can occasionally fail on some operating systems/python environments.

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
[![python-3.7-x86-Build_Failed](https://img.shields.io/badge/python--3.7--x86_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![windows-2019-python-3.8-x86](https://img.shields.io/badge/build-python--3.8--x86_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.8_x86/pytest_report.html)
[![windows-2019-python-3.8-x64](https://img.shields.io/badge/build-python--3.8--x64_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.8_x64/pytest_report.html)
[![windows-2019-python-3.9-x86](https://img.shields.io/badge/build-python--3.9--x86_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.9_x86/pytest_report.html)
[![windows-2019-python-3.9-x64](https://img.shields.io/badge/build-python--3.9--x64_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.9_x64/pytest_report.html)
[![python-3.10-x86-Build_Failed](https://img.shields.io/badge/python--3.10--x86_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![windows-2019-python-3.10-x64](https://img.shields.io/badge/build-python--3.10--x64_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.10_x64/pytest_report.html)
[![windows-2019-python-3.11-x86](https://img.shields.io/badge/build-python--3.11--x86_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.11_x86/pytest_report.html)
[![windows-2019-python-3.11-x64](https://img.shields.io/badge/build-python--3.11--x64_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.11_x64/pytest_report.html)
[![windows-2019-python-3.12-x86](https://img.shields.io/badge/build-python--3.12--x86_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.12_x86/pytest_report.html)
[![windows-2019-python-3.12-x64](https://img.shields.io/badge/build-python--3.12--x64_Passing_663-brightgreen?style=plastic&logo=simple-icons&logoColor=%23FF5e34&label=21&labelColor=%23c71818&color=%232f991a)](https://htmlpreview.github.io/?https://github.com/NickHugi/PyKotor/blob/e0890252659c03e8a9bfbeea6b8d23814200a3de/tests/results/59dfa506d7321a00660c3225c653280e1e90df28/pytest_report_windows-2019_python_3.12_x64/pytest_report.html)
<!-- WINDOWS-BADGES-END -->

### Linux:

<!-- LINUX-BADGES-START -->
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.8-x64-Build_Failed](https://img.shields.io/badge/python--3.8--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.9-x64-Build_Failed](https://img.shields.io/badge/python--3.9--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.10-x64-Build_Failed](https://img.shields.io/badge/python--3.10--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.11-x64-Build_Failed](https://img.shields.io/badge/python--3.11--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.12-x64-Build_Failed](https://img.shields.io/badge/python--3.12--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
<!-- LINUX-BADGES-END -->

### MacOS:

<!-- MACOS-BADGES-START -->
[![python-3.7-x64-Build_Failed](https://img.shields.io/badge/python--3.7--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.8-x64-Build_Failed](https://img.shields.io/badge/python--3.8--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.9-x64-Build_Failed](https://img.shields.io/badge/python--3.9--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.10-x64-Build_Failed](https://img.shields.io/badge/python--3.10--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.11-x64-Build_Failed](https://img.shields.io/badge/python--3.11--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
[![python-3.12-x64-Build_Failed](https://img.shields.io/badge/python--3.12--x64_Build_Failed-lightgrey)](https://github.com/NickHugi/PyKotor/actions/runs/14437977049)
<!-- MACOS-BADGES-END -->

## License
This repository falls under the [LGPL-3.0-or-later License](https://github.com/NickHugi/PyKotor/blob/master/LICENSE).






















































