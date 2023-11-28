PyKotor
=======
A Python library that can read and modify most file formats used by the game Knights of the Old Republic and its sequel.

## Installation
Install from [PyPI](https://pypi.org/project/PyKotor/).
```bash
pip install pykotor
```

## Requirements
PyKotor supports any Python version within 3.8 through 3.12. See requirements.txt for additional pip dependencies.
PyKotor is supported on most operating systems, including Mac OS and Linux.

## Example Usage
Simple example of loading data from a game directory, searching for a specific texture and exporting it to the TGA format.
```python
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.resource.formats.tpc import write_tpc

inst = Installation("C:/Program Files (x86)/Steam/steamapps/common/swkotor")
tex = inst.texture("C_Gammorean01")
write_tpc(tex, "./C_Gammorean01.tga", ResourceType.TGA)
```
As shown, this will save C_Gammorean01.tga to the current directory.

## Cloning the repo
If you would like to work with the source files directly from GitHub, run the following commands to get yourself set:
```bash
git clone https://github.com/NickHugi/PyKotor
cd PyKotor
pip install -r requirements.txt
pip install -r tools/HolocronToolset/toolset/requirements.txt
```
Then, you can run any entry-point scripts, such as HoloPatcher and the Toolset, like this:
```bash
python -m tools.holopatcher
python -m tools.HolocronToolset.toolset
```

## Troubleshooting
If you find yourself unable to run certain entry-point scripts on this repo in your python interpreter (e.g. HoloPatcher or Holocron Toolset), you may be missing some system-level dependencies. **These are *not* required when using the compiled releases**
### Holocron Toolset
Holocron Toolset requires PyQt5.
#### Linux:
- On Debian-based Linux distros, install `python3-pyqt5`
```commandline
sudo apt install python3-pyqt5
```
#### Mac OS:
- If you've installed Python with HomeBrew (you should have), install PyQt5:
```commandline
brew install pyqt5
```
### HoloPatcher
HoloPatcher requires `tkinter`
#### Linux:
```commandline
sudo apt install python3-tkinter
```
#### Mac OS:
- If you've installed Python with HomeBrew (you should have), install tkinter:
```commandline
brew install python-tk
```

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
