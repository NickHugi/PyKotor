# HoloGenerator - KOTOR Configuration Generator for HoloPatcher

HoloGenerator is a **GUI-only** tool for automatically generating `changes.ini` files compatible with HoloPatcher by comparing two KOTOR installations or individual files.

## 🌟 Features

### Multiple Interfaces

- **Desktop GUI**: User-friendly tkinter-based interface
- **Web Application**: Modern React-based web interface with real-time diffing

**Note:** HoloGenerator is designed exclusively for GUI usage. If you need command-line functionality, please use [KotorDiff](https://github.com/th3w1zard1/PyKotor/tree/main/Tools/KotorDiff) instead.

### Advanced Diffing

- **Real-time comparison**: Fast, visual side-by-side file comparison
- **Multi-format Support**: GFF, 2DA, TLK, SSF, LIP, and other KOTOR file formats
- **Word-level diffing**: Granular change detection and highlighting
- **Intelligent caching**: Optimized performance for large files

### Workflow Features

- **Undo/Redo**: Full history tracking with keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- **Sequential file addition**: Build complex configurations by adding multiple file diffs
- **Import/Export**: Support for importing existing `changes.ini` files
- **Copy/Download**: Easy sharing and distribution of generated configurations

### Web Interface

- **Intuitive UI**: Clean, modern interface inspired by GitHub's diff viewer
- **Drag & Drop**: Easy file uploads with format auto-detection
- **Live Preview**: Real-time configuration generation and preview
- **Mobile Friendly**: Responsive design that works on all devices

## 🚀 Quick Start

### Web Interface

Visit: **<https://th3w1zard1.github.io/hologenerator>**

### Desktop GUI

```bash
python -m hologenerator
```

## 📦 Installation

### From Source

```bash
cd Tools/HoloGenerator
pip install -e .
```

### Development Setup

```bash
cd Tools/HoloGenerator
python setup_dev.py
```

## 🔧 Usage Examples

### Desktop GUI

**Launch the application:**

```bash
python -m hologenerator
```

**Using the GUI:**

1. Select your original and modified KOTOR installations or files
2. View real-time differences in the diff viewer
3. Generate a complete `changes.ini` configuration file
4. Save or copy the generated configuration

### Web Interface Workflow

1. **Upload/Paste Files**: Add your original and modified file content
2. **Real-time Diff**: See changes highlighted instantly
3. **Build Configuration**: Add multiple file diffs sequentially
4. **Generate Config**: Create a complete `changes.ini` file
5. **Download/Copy**: Get your configuration for distribution

## 🗂️ File Format Support

| Format | Description | Support Level | Example Files |
|--------|-------------|---------------|---------------|
| **GFF** | Game resource files | ✅ Full | `.utc`, `.uti`, `.dlg`, `.are`, `.git`, `.ifo`, `.jrl` |
| **2DA** | Table files | ✅ Full | `appearance.2da`, `classes.2da`, `spells.2da` |
| **TLK** | Dialog/string files | ✅ Full | `dialog.tlk`, `dialogf.tlk` |
| **SSF** | Sound set files | ✅ Full | `.ssf` files |
| **LIP** | Lip-sync files | ✅ Full | `.lip` files |
| **Others** | Binary files | ⚡ Hash comparison | Any other format |

## 🏗️ Architecture

### Core Components

```bash
hologenerator/
├── core/
│   ├── differ.py          # File comparison engine
│   ├── changes_ini.py     # HoloPatcher config generation  
│   └── generator.py       # Main configuration generator
├── gui/
│   └── main.py           # Tkinter-based desktop interface
└── web/                  # React web application
    ├── src/components/   # React components
    ├── src/hooks/        # Custom React hooks
    └── src/utils/        # Utility functions
```

### Generated Configuration Structure

The tool generates standard HoloPatcher sections:

```ini
[Settings]
WindowCaption=Generated Mod Configuration
ConfirmMessage=This mod was generated from file differences.

[InstallList]
File1=Override

[Override]
File1=modified_file.txt

[GFFList]
File1=character.utc

[character.utc]
ModifyField1=FieldModification1

[2DAList]
File1=appearance.2da

[appearance.2da]
ChangeRow1=RowModification1

[TLKList]
StrRef42=Modified
```

## 🧪 Testing

### Run All Tests

```bash
./run_tests.sh
```

### Individual Test Suites

```bash
# Python tests
python -m pytest src/hologenerator/tests/ -v

# React tests
cd web && npm test

# GUI tests (if tkinter available)
python -m unittest src/hologenerator/tests/test_gui.py
```

### Test Coverage

- **Core functionality**: 100% coverage of critical paths
- **Error handling**: Comprehensive error scenario testing
- **Integration tests**: End-to-end workflow validation
- **Cross-platform**: Windows, Linux, and macOS compatibility

## 🌐 Web Deployment

The React web application is automatically deployed to GitHub Pages via GitHub Actions:

### Automatic Deployment

- **Trigger**: Push to main branch with changes in `Tools/HoloGenerator/web/`
- **Build**: React production build with optimizations
- **Deploy**: GitHub Pages deployment to `https://th3w1zard1.github.io/hologenerator`

### Manual Deployment

```bash
cd web
npm run build
npm run deploy
```

## 🛠️ Development

### Prerequisites

- **Python 3.8+** (required)
- **Node.js 16+** (for web interface)
- **tkinter** (required, for GUI)

### Development Setup

```bash
# Setup development environment
python setup_dev.py

# Start React development server
cd web && npm start

# Run in development mode
python -m hologenerator
```

### Code Quality

- **Linting**: flake8, ESLint
- **Formatting**: black, Prettier
- **Type Checking**: mypy, TypeScript
- **Testing**: pytest, Jest
- **Pre-commit Hooks**: Automatic testing before commits

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Setup** development environment (`python setup_dev.py`)
4. **Make** your changes with tests
5. **Test** your changes (`./run_tests.sh`)
6. **Commit** your changes (`git commit -m 'Add amazing feature'`)
7. **Push** to the branch (`git push origin feature/amazing-feature`)
8. **Open** a Pull Request

## 📝 License

This project is part of the PyKotor toolkit and follows the same licensing terms.

## 🙏 Acknowledgments

- **PyKotor Team**: For the core KOTOR file format libraries
- **HoloPatcher**: For the configuration format specification
- **KOTOR Community**: For feedback and testing

## 🔗 Links

- **Web App**: <https://th3w1zard1.github.io/hologenerator>
- **Documentation**: [Full documentation](https://github.com/th3w1zard1/PyKotor/tree/main/Tools/HoloGenerator)
- **Issues**: [Report bugs](https://github.com/th3w1zard1/PyKotor/issues)
- **PyKotor**: [Main project](https://github.com/th3w1zard1/PyKotor)
- **KotorDiff**: [CLI alternative](https://github.com/th3w1zard1/PyKotor/tree/main/Tools/KotorDiff)
