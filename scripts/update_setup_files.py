"""Helper script to create setup.py files that read from requirements.txt."""
from __future__ import annotations

from pathlib import Path

SETUP_PY_TEMPLATE = '''from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup


def read_requirements() -> list[str]:
    """Read requirements from requirements.txt file."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    if not requirements_path.exists():
        return []
    
    requirements = []
    with open(requirements_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                requirements.append(line)
    return requirements


setup(
    name="{name}",
    version="{version}",
    description="{description}",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    install_requires=read_requirements(),
    python_requires=">=3.8",
{extra}
)
'''

SETUPS = [
    {
        "path": Path("Libraries/PyKotor/setup.py"),
        "name": "pykotor",
        "version": "1.8.0",
        "description": "Read, modify and write files used by KotOR's game engine.",
        "extra": "",
    },
    {
        "path": Path("Libraries/PyKotorGL/setup.py"),
        "name": "pykotorgl",
        "version": "1.8.0",
        "description": "OpenGL rendering module for PyKotor - renders KotOR modules and scenes.",
        "extra": "",
    },
    {
        "path": Path("Libraries/PyKotorFont/setup.py"),
        "name": "pykotorfont",
        "version": "1.8.0",
        "description": "Font rendering module for PyKotor - handles TXI/TGA font generation.",
        "extra": "",
    },
]

for setup_info in SETUPS:
    content = SETUP_PY_TEMPLATE.format(**setup_info)
    setup_info["path"].write_text(content, encoding="utf-8")
    print(f"Created {setup_info['path']}")

