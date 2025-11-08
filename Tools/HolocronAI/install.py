"""Installation script for HolocronAI."""
from __future__ import annotations

import subprocess
import sys

from pathlib import Path


def install_dependencies():
    """Install required dependencies."""
    try:
        # Install requirements
        subprocess.check_call(  # noqa: S603
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                "requirements.txt",
            ]
        )
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    else:
        return True


def install_package() -> bool:
    """Install HolocronAI in development mode."""
    try:
        # Install package
        subprocess.check_call(  # noqa: S603
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-e",
                ".",
            ]
        )
        print("HolocronAI installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing package: {e}")
        return False
    else:
        return True


def main() -> None:
    print("Installing HolocronAI...")

    # Ensure we're in the correct directory
    script_dir: Path = Path(__file__).parent
    if not (script_dir / "requirements.txt").exists():
        print("Error: requirements.txt not found!")
        return

    # Install dependencies
    print("\nInstalling dependencies...")
    if not install_dependencies():
        return

    # Install package
    print("\nInstalling HolocronAI...")
    if not install_package():
        return

    print("\nInstallation complete! You can now run HolocronAI using:")
    print("python -m holocron_ai  # For GUI mode")
    print("python -m holocron_ai --cli  # For CLI mode")

if __name__ == "__main__":
    main()
