from __future__ import annotations

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
    name="gui-converter",
    version="1.0.0",
    description="GUI Converter Tool for KotOR",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=read_requirements(),
    python_requires=">=3.8",
)
