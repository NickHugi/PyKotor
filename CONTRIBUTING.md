# Contributing to PyKotor

Thank you for your interest in contributing to PyKotor! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful, inclusive, and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/PyKotor.git
   cd PyKotor
   ```
3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/th3w1zard1/PyKotor.git
   ```

## Development Setup

PyKotor supports multiple package managers. Choose the one that works best for you:

### Option 1: Using `uv` (Recommended)

`uv` is a fast Python package installer and resolver written in Rust.

1. **Install uv** (if not already installed):
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Activate the virtual environment**:
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

4. **Install the project in editable mode**:
   ```bash
   # Install core library
   uv pip install -e Libraries/PyKotor
   
   # Install with optional extensions
   uv pip install -e Libraries/PyKotor -e Libraries/PyKotorGL -e Libraries/PyKotorFont
   
   # Install specific tools
   uv pip install -e Tools/HolocronToolset
   uv pip install -e Tools/HoloPatcher
   ```

### Option 2: Using Poetry

Poetry is a dependency management and packaging tool.

1. **Install Poetry** (if not already installed):
   ```bash
   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   
   # macOS/Linux
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

4. **Install with optional dependencies**:
   ```bash
   # Install with all extensions
   poetry install --extras "all-extensions"
   
   # Install with specific tools
   poetry install --extras "holocrontoolset"
   ```

### Option 3: Using pip

Standard pip installation for those who prefer it.

1. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   # Install core library
   pip install -e Libraries/PyKotor
   
   # Install with extensions
   pip install -e Libraries/PyKotor[font,gl]
   
   # Install specific tools (they will pull in their dependencies)
   pip install -e Tools/HolocronToolset
   pip install -e Tools/HoloPatcher
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e .[dev]
   ```

## Project Structure

```
PyKotor/
├── Libraries/              # Core libraries
│   ├── PyKotor/          # Main library (pykotor)
│   ├── PyKotorGL/        # OpenGL rendering (pykotorgl)
│   ├── PyKotorFont/      # Font rendering (pykotorfont)
│   └── Utility/           # Shared utilities
├── Tools/                 # Standalone tools
│   ├── HolocronToolset/  # Main GUI editor
│   ├── HoloPatcher/      # TSLPatcher alternative
│   ├── BatchPatcher/     # Batch translation tool
│   ├── KotorDiff/        # Diff generation tool
│   └── GuiConverter/    # GUI conversion tool
├── tests/                # Test suite
├── docs/                 # Documentation
└── scripts/              # Helper scripts
```

### Package Dependencies

- **PyKotor**: Core library (no optional deps required)
- **PyKotorGL**: Requires `pykotor>=1.8.0`, `numpy`, `PyOpenGL`, `PyGLM`
- **PyKotorFont**: Requires `pykotor>=1.8.0`, `pillow`
- **HolocronToolset**: Requires `pykotor>=1.8.0`, `pykotorgl>=1.8.0`, Qt bindings
- **HoloPatcher**: Requires `pykotor>=1.8.0`
- **BatchPatcher**: Requires `pykotor>=1.8.0`, `pykotorfont>=1.8.0`

## Making Changes

1. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines

3. **Test your changes**:
   ```bash
   # Run all tests
   pytest
   
   # Run specific test suite
   pytest tests/test_pykotor/
   
   # Run with coverage
   pytest --cov=pykotor --cov-report=html
   ```

4. **Update documentation** if needed

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

   Use clear, descriptive commit messages. Follow the format:
   ```
   type(scope): brief description
   
   Longer explanation if needed
   ```

   Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_pykotor/test_resource_formats.py

# Specific test
pytest tests/test_pykotor/test_resource_formats.py::TestTPC::test_read_tpc

# With verbose output
pytest -v

# With coverage
pytest --cov=pykotor --cov-report=term-missing
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the existing test structure
- Use descriptive test names
- Test both success and failure cases
- Include edge cases

Example test structure:
```python
from pykotor.resource.formats.tpc import read_tpc

def test_read_tpc_success():
    """Test reading a valid TPC file."""
    # Arrange
    test_file = Path("tests/files/test.tpc")
    
    # Act
    tpc = read_tpc(test_file)
    
    # Assert
    assert tpc is not None
    assert tpc.width == 512
```

## Code Style

PyKotor uses `ruff` for linting and formatting. Configuration is in `pyproject.toml`.

### Formatting

```bash
# Format code
ruff format .

# Check formatting
ruff format --check .
```

### Linting

```bash
# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Key Style Guidelines

- **Line length**: 175 characters (configured in `pyproject.toml`)
- **Imports**: Use `from __future__ import annotations` at the top
- **Type hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings
- **Naming**: Follow PEP 8 (snake_case for functions/variables, PascalCase for classes)

### Pre-commit Hooks (Optional)

You can set up pre-commit hooks to automatically format and lint:

```bash
pip install pre-commit
pre-commit install
```

## Submitting Changes

1. **Update your branch** with the latest changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots if UI changes
   - Ensure all tests pass
   - Update documentation as needed

4. **Respond to feedback** and make requested changes

## Documentation

### Code Documentation

- Use Google-style docstrings
- Document all public functions, classes, and methods
- Include parameter descriptions and return types
- Add examples for complex functions

Example:
```python
def read_tpc(file_path: Path) -> TPC:
    """Read a TPC texture file from disk.
    
    Args:
        file_path: Path to the TPC file to read
        
    Returns:
        TPC object containing texture data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file is not a valid TPC
    """
```

### User Documentation

- Update `README.md` for user-facing changes
- Add examples to `docs/` for new features
- Update tool-specific READMEs in `Tools/` directories

## Development Workflow

### Working on a Library

1. Navigate to the library directory:
   ```bash
   cd Libraries/PyKotor
   ```

2. Install in editable mode:
   ```bash
   pip install -e .
   ```

3. Make your changes

4. Test your changes:
   ```bash
   pytest ../../tests/test_pykotor/
   ```

### Working on a Tool

1. Navigate to the tool directory:
   ```bash
   cd Tools/HolocronToolset
   ```

2. Install in editable mode:
   ```bash
   pip install -e .
   ```

3. Make your changes

4. Test your changes:
   ```bash
   pytest ../../tests/test_toolset/
   ```

## Building Packages

### Building with setuptools

```bash
# Build wheel
python -m build

# Build source distribution
python -m build --sdist
```

### Building with Poetry

```bash
poetry build
```

### Building with uv

```bash
uv build
```

## Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check `docs/` for detailed guides

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3.0-or-later License.

Thank you for contributing to PyKotor! 🎉

