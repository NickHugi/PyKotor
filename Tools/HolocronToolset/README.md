# HolocronToolset

A PyQt5 application that can edit the files used by the KotOR game engine.

## Requirements

- Python 3.8 through 3.12

## Local Run

### Windows

From command line:

```
pip install -r requirements.txt
set PYTHONPATH=%cd%
python toolset/__main__.py
```

### Unix

From terminal:

```
pip install -r requirements.txt
PYTHONPATH=$PWD python toolset/__main__.py
```

## Local Development

- Clone [PyKotor](https://github.com/NickHugi/PyKotor) and run the `install_python_venv.ps1` script in your powershell terminal. That's it!


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
