# Development Setup Guide

This guide covers setting up the PyKotor development environment using different package managers.

## Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Git** for version control
- One of the following package managers:
  - `uv` (recommended - fastest)
  - `poetry` (good for dependency management)
  - `pip` (standard, always available)

## Quick Start

### Using `uv` (Fastest - Recommended)

`uv` is a modern Python package installer written in Rust, offering significantly faster dependency resolution and installation.

#### Installation

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   ```

2. **Sync dependencies:**
   ```bash
   uv sync
   ```
   This will:
   - Create a virtual environment (`.venv`)
   - Install all dependencies from `pyproject.toml`
   - Install the workspace in editable mode

3. **Activate the virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Verify installation:**
   ```bash
   python -c "import pykotor; print(pykotor.__version__)"
   ```

#### Installing Specific Packages

```bash
# Install core library only
uv pip install -e Libraries/PyKotor

# Install with OpenGL support
uv pip install -e Libraries/PyKotor -e Libraries/PyKotorGL

# Install with font support
uv pip install -e Libraries/PyKotor -e Libraries/PyKotorFont

# Install a specific tool
uv pip install -e Tools/HolocronToolset

# Install everything
uv pip install -e Libraries/PyKotor -e Libraries/PyKotorGL -e Libraries/PyKotorFont -e Tools/HolocronToolset -e Tools/HoloPatcher
```

#### Installing Development Dependencies

```bash
uv pip install -e .[dev]
```

#### Running Tests with uv

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/test_pykotor/

# Run with coverage
uv run pytest --cov=pykotor --cov-report=html
```

### Using Poetry

Poetry provides excellent dependency management and virtual environment handling.

#### Installation

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Add to PATH** (if needed):
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
```

#### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```
   This installs:
   - Core dependencies
   - Development dependencies
   - The workspace in editable mode

3. **Activate the virtual environment:**
   ```bash
   poetry shell
   ```

   Or run commands within the environment:
   ```bash
   poetry run python -c "import pykotor; print(pykotor.__version__)"
   ```

#### Installing with Optional Dependencies

```bash
# Install with all extensions
poetry install --extras "all-extensions"

# Install with specific tools
poetry install --extras "holocrontoolset"

# Install everything
poetry install --extras "all"
```

#### Installing Individual Packages

```bash
# Install core library
cd Libraries/PyKotor
poetry install

# Install with dependencies
cd Libraries/PyKotorGL
poetry install
```

#### Running Tests with Poetry

```bash
# Run all tests
poetry run pytest

# Run specific test suite
poetry run pytest tests/test_pykotor/

# Run with coverage
poetry run pytest --cov=pykotor --cov-report=html
```

### Using pip

Standard pip installation - works everywhere Python is available.

#### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/th3w1zard1/PyKotor.git
   cd PyKotor
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Upgrade pip and build tools:**
   ```bash
   pip install --upgrade pip setuptools wheel build
   ```

4. **Install core library:**
   ```bash
   pip install -e Libraries/PyKotor
   ```

5. **Install optional extensions:**
   ```bash
   # With OpenGL support
   pip install -e Libraries/PyKotorGL
   
   # With font support
   pip install -e Libraries/PyKotorFont
   ```

6. **Install development dependencies:**
   ```bash
   pip install -e .[dev]
   ```

#### Installing from requirements.txt

Each package has a `requirements.txt` that matches its `pyproject.toml`:

```bash
# Install core library dependencies
pip install -r Libraries/PyKotor/requirements.txt
pip install -e Libraries/PyKotor

# Install tool dependencies
pip install -r Tools/HolocronToolset/requirements.txt
pip install -e Tools/HolocronToolset
```

#### Running Tests with pip

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_pykotor/

# Run with coverage
pytest --cov=pykotor --cov-report=html
```

## Package Structure

### Libraries

Each library is a standalone package:

- **Libraries/PyKotor/** - Core library (`pykotor`)
- **Libraries/PyKotorGL/** - OpenGL rendering (`pykotorgl`)
- **Libraries/PyKotorFont/** - Font rendering (`pykotorfont`)

### Tools

Each tool is a standalone application:

- **Tools/HolocronToolset/** - Main GUI editor
- **Tools/HoloPatcher/** - TSLPatcher alternative
- **Tools/BatchPatcher/** - Batch translation tool
- **Tools/KotorDiff/** - Diff generation tool
- **Tools/GuiConverter/** - GUI conversion tool

## Dependency Management

### Understanding Dependencies

Dependencies are defined in two places (kept in sync):

1. **`pyproject.toml`** - PEP 621 standard format
2. **`requirements.txt`** - Traditional pip format

Both files are automatically synchronized. The `setup.py` files read from `requirements.txt`.

### Core Dependencies

**PyKotor** (core library):
- `loggerplus>=0.1.3` - Logging utilities
- `ply>=3.11,<4` - Parser generator for NSS compiler

**PyKotorGL** (OpenGL extension):
- `pykotor>=1.8.0` - Core library
- `numpy>=1.22` - Numerical operations
- `PyOpenGL~=3.1` - OpenGL bindings
- `PyGLM>=2.0,<2.8` - GLM math library (CPython only)

**PyKotorFont** (font extension):
- `pykotor>=1.8.0` - Core library
- `pillow>=9.5` - Image processing (CPython)
- `pillow>10,<11.1.0` - Image processing (PyPy)

### Tool Dependencies

**HolocronToolset**:
- `pykotor>=1.8.0`
- `pykotorgl>=1.8.0`
- Qt bindings (PyQt5/PySide6)
- Various UI libraries

**HoloPatcher**:
- `pykotor>=1.8.0`
- `requests` - For update checking
- `charset-normalizer` - Encoding detection

**BatchPatcher**:
- `pykotor>=1.8.0`
- `pykotorfont>=1.8.0`
- Translation libraries
- Image processing tools

## Development Workflow

### Working on a Library

1. Navigate to the library:
   ```bash
   cd Libraries/PyKotor
   ```

2. Install in editable mode:
   ```bash
   # With uv
   uv pip install -e .
   
   # With poetry
   poetry install
   
   # With pip
   pip install -e .
   ```

3. Make your changes

4. Test your changes:
   ```bash
   pytest ../../tests/test_pykotor/
   ```

### Working on a Tool

1. Navigate to the tool:
   ```bash
   cd Tools/HolocronToolset
   ```

2. Install in editable mode:
   ```bash
   # With uv
   uv pip install -e .
   
   # With poetry
   poetry install
   
   # With pip
   pip install -e .
   ```

3. Make your changes

4. Test your changes:
   ```bash
   pytest ../../tests/test_toolset/
   ```

## Troubleshooting

### Common Issues

#### Virtual Environment Not Found

**Problem:** `uv sync` or `poetry install` fails to create venv

**Solution:**
```bash
# With uv
uv venv
uv pip install -e .

# With poetry
poetry env use python3.9  # or your Python version
poetry install

# With pip
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

#### Dependency Conflicts

**Problem:** Conflicting package versions

**Solution:**
```bash
# With uv (handles conflicts automatically)
uv sync --upgrade

# With poetry
poetry update

# With pip
pip install --upgrade --force-reinstall -e .
```

#### Import Errors

**Problem:** `ModuleNotFoundError` when importing pykotor

**Solution:**
```bash
# Ensure package is installed in editable mode
pip install -e Libraries/PyKotor

# Verify installation
python -c "import pykotor; print(pykotor.__file__)"
```

#### Platform-Specific Dependencies

Some dependencies have platform-specific requirements:

- **PyGLM**: Only available for CPython (not PyPy)
- **PyQt5**: Windows/macOS/Linux have different packages
- **Pillow**: Different versions for CPython vs PyPy

These are handled automatically by the package managers using environment markers in `pyproject.toml`.

## Building Packages

### Building with setuptools

```bash
# Install build tools
pip install build

# Build wheel and source distribution
python -m build
```

### Building with Poetry

```bash
poetry build
```

### Building with uv

```bash
uv build
```

Output will be in the `dist/` directory.

## Next Steps

- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
- Check [README.md](../README.md) for project overview
- Explore the [docs/](.) directory for detailed documentation
- Run tests: `pytest` or `poetry run pytest`

## Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/th3w1zard1/PyKotor/issues)
- **Discussions**: [Ask questions](https://github.com/th3w1zard1/PyKotor/discussions)
- **Documentation**: Check the `docs/` directory

