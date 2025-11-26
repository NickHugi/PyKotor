# Setting Up PowerShell for PyKotor

## Overview

PowerShell is a task automation and configuration management framework from Microsoft, consisting of a command-line shell and the associated scripting language. For Windows users working with PyKotor, certain scripts and utilities may require PowerShell. This guide will help you set up PowerShell on your system and address common issues related to script execution policies.

## Installing PowerShell

### Windows

PowerShell comes pre-installed on most modern versions of Windows. However, if you need to install or update PowerShell, follow these steps:

1. Visit the [official PowerShell GitHub page](https://github.com/PowerShell/PowerShell).
2. Download the latest release suitable for your Windows version.
3. Run the installer and follow the on-screen instructions.

### Linux/Mac

1. Open a terminal window.
2. Run the following command to install PowerShell:

   # For Ubuntu-based distributions:
   ```bash
   sudo apt-get install -y powershell
   ```

   # For Fedora
   ```bash
   sudo dnf install -y powershell
   ```

   # For macOS
   ```bash
   brew install --cask powershell
   ```
   
   or

   ```bash
   brew install pwsh
   ```

3. Once installed, you can launch PowerShell by typing `pwsh` in your terminal.

#### Alternatives

If you are struggling to get Powershell setup on your system, and you're using linux/mac, try running our automated installer instead:
```bash
./install_powershell.sh
```

## Running PowerShell Scripts

To run PowerShell scripts (`.ps1` files), you might need to change the execution policy. By default, PowerShell restricts the execution of scripts to prevent unauthorized scripts from running on your system.

1. Open PowerShell as an administrator.
2. Run the following command to allow script execution:

   ```powershell
   Set-ExecutionPolicy Unrestricted
   ```

3. Choose `Y` when prompted to change the execution policy.

This command allows our scripts to run on your system. If you do not have admin privileges, see the next section.

## Common Issues

### Script Not Digitally Signed

If you encounter an error stating that a script is not digitally signed, you can bypass this error temporarily by running the script with the following command:

```powershell
PowerShell.exe -ExecutionPolicy Bypass -File path\to\your\script.ps1
```

Replace `path\to\your\script.ps1` with the actual path to the script you want to run.

## Using PowerShell for PyKotor Development

When working with the PyKotor source files directly from GitHub, you may need to run PowerShell scripts for setting up the development environment. For instance, `install_python_venv.ps1` is a PowerShell script that automates the creation of a Python virtual environment and sets up necessary environment variables for PyKotor development.

### Running `install_python_venv.ps1`

1. Clone the PyKotor repository and navigate to the project directory.
2. Run the following command(s):

#### Windows:

   ```powershell
   ./install_python_venv.ps1
   ```
#### Mac/Linux:

```bash
pwsh
./install_python_venv.ps1
```

This script checks for the appropriate Python version, installs it if necessary, and sets up a virtual environment for PyKotor development.

## Conclusion

This guide provided an overview of how to install PowerShell on different operating systems, how to configure your system to run PowerShell scripts, and how to use PowerShell for setting up the PyKotor development environment. For more detailed information, refer to the [official PowerShell documentation](https://learn.microsoft.com/en-us/powershell/).