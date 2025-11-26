#!/bin/bash
# Bash script to set up development environment
# Usage: ./scripts/setup_dev_environment.sh

set -e

SKIP_PRECOMMIT=false
SKIP_VENV=false
VENV_NAME=".venv"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-precommit)
            SKIP_PRECOMMIT=true
            shift
            ;;
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --venv-name)
            VENV_NAME="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Setting up PyKotor development environment..."

# Check Python installation
echo ""
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"

# Create virtual environment
if [ "$SKIP_VENV" = false ]; then
    echo ""
    echo "Creating virtual environment..."
    if [ -d "$VENV_NAME" ]; then
        echo "Virtual environment already exists at $VENV_NAME"
    else
        python3 -m venv "$VENV_NAME"
        echo "Virtual environment created at $VENV_NAME"
    fi
    
    echo "Activating virtual environment..."
    source "$VENV_NAME/bin/activate"
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

# Install development dependencies
echo ""
echo "Installing development dependencies..."
pip install -e Libraries/PyKotor
pip install -e Libraries/PyKotorGL
pip install -e Libraries/PyKotorFont
pip install -e .[dev]

# Install pre-commit hooks
if [ "$SKIP_PRECOMMIT" = false ]; then
    echo ""
    echo "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
    echo "Pre-commit hooks installed"
fi

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import pykotor; print('✓ PyKotor installed')" || exit 1
python -c "import pykotor.gl; print('✓ PyKotorGL installed')" 2>/dev/null || echo "PyKotorGL optional (requires OpenGL dependencies)"
python -c "import pykotor.font; print('✓ PyKotorFont installed')" 2>/dev/null || echo "PyKotorFont optional (requires Pillow)"

echo ""
echo "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment: source $VENV_NAME/bin/activate"
echo "  2. Run tests: pytest tests/"
echo "  3. Run linter: ruff check ."
echo "  4. Check formatting: ruff format --check ."

