# HolocronToolset

A PyQt5 application that can edit the files used by the KotOR game engine.

## Requirements

- Python 3

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

- Clone [PyKotor](https://github.com/NickHugi/PyKotor) and [PyKotorGL](https://github.com/NickHugi/PyKotorGL) repositories
- Create symbolic link to `PyKotorGL/pykotor/gl` directory in `PyKotor/pykotor`
- Create symbolic link to `PyKotor/pykotor` directory in `HolocronToolset`

### Windows

```
cd %SOURCE_DIR%\PyKotor\pykotor
mklink gl /D %SOURCE_DIR%\PyKotorGL\pykotor\gl
cd %SOURCE_DIR%\HolocronToolset
mklink pykotor /D %SOURCE_DIR%\PyKotor\pykotor
```