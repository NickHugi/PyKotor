import os
import subprocess
import sys

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}")
        print(stderr.decode())
        sys.exit(1)
    return stdout.decode()

def setup_dev_env():
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
