from __future__ import annotations

import subprocess
import sys


def run_command(command: str) -> str:
    """Run a command and return the output."""
    print(f"Running command: {command}")
    process = subprocess.run(  # noqa: S603
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(process.stderr)
        sys.exit(1)
    return process.stdout


def setup_dev_env():
    """Setup the development environment."""
    # Install main package in editable mode
    run_command("pip install -e .")

    # Install PyKotor packages
    run_command("pip install -e Libraries/PyKotor")
    run_command("pip install -e Libraries/PyKotorFont")
    run_command("pip install -e Libraries/PyKotorGL")

    # Install Utility package
    run_command("pip install -e Libraries/Utility")

    # Install Tool packages
    run_command("pip install -e Tools/HolocronToolset")
    run_command("pip install -e Tools/HoloPatcher")
    run_command("pip install -e Tools/KotorDiff")
    run_command("pip install -e Tools/BatchPatcher")

    print("Development environment setup complete.")


if __name__ == "__main__":
    setup_dev_env()
