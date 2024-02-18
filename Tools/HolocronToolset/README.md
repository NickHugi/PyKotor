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

### Note for Alpine users:
You might get this error:
```
pyproject.toml: line 7: using '[tool.sip.metadata]' to specify the project metadata is deprecated and will be removed in SIP v7.0.0, use '[project]' instead
```
While we're not sure what the exact problem is, it seems newer python versions won't correctly be able to build pyqt5. If you don't have a binary available (--only-binary=:all: returns no versions) you'll need to downgrade python preferably to 3.8 or you won't be able to use qt5!
[See this issue for more information](https://github.com/altendky/pyqt-tools/issues/100)

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
