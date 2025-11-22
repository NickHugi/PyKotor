# HoloPazaak

A PyQt5 implementation of the Pazaak card game from Knights of the Old Republic.

## Requirements

- Python 3.8 through 3.12

## Local Run

### Windows

From command line:

```
pip install -r requirements.txt
set PYTHONPATH=%cd%\src
python src/holopazaak/app.py
```

### Unix

From terminal:

```
pip install -r requirements.txt
PYTHONPATH=$PWD/src python src/holopazaak/app.py
```

## Local Development

- Clone [PyKotor](https://github.com/NickHugi/PyKotor) and run the `install_python_venv.ps1` script in your powershell terminal. That's it!

## Building

To build the executable:

```powershell
./Tools/HoloPazaak/compile/build.ps1
```

The output will be in `dist/HoloPazaak/`.

