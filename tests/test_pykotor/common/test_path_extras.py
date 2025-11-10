from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

import contextlib

from utility.system.path import Path
from pykotor.tools.path import CaseAwarePath
from pathlib import Path, PosixPath, PurePath, PurePosixPath, PureWindowsPath, WindowsPath


class TestPathExtras(unittest.TestCase):
    def create_and_run_batch_script(self, cmd: list[str], pause_after_command: bool = False):
        with TemporaryDirectory() as tempdir:
            # Ensure the script path is absolute
            script_path = str(Path(tempdir, "temp_script.bat").absolute())

            # Write the commands to a batch file
            with open(script_path, "w") as file:
                for command in cmd:
                    file.write(command + "\n")
                if pause_after_command:
                    file.write("pause\nexit\n")

            # Determine the CMD switch to use
            cmd_switch = "/K" if pause_after_command else "/C"

            # Construct the command to run the batch script with elevated privileges
            run_script_cmd: list[str] = ["Powershell", "-Command", f"Start-Process cmd.exe -ArgumentList '{cmd_switch} \"{script_path}\"' -Verb RunAs -Wait"]

            # Execute the batch script
            subprocess.run(run_script_cmd, check=False)

            # Optionally, delete the batch script after execution
            with contextlib.suppress(Exception):
                os.remove(script_path)

    def remove_permissions(self, path_str: str):
        is_file = os.path.isfile(path_str)

        # Define the commands
        combined_commands: list[str] = [
            f'icacls "{path_str}" /reset',
            f'attrib +S +R "{path_str}"',
            f'icacls "{path_str}" /inheritance:r',
            f'icacls "{path_str}" /deny Everyone:(F)',
        ]

        # Create and run the batch script
        self.create_and_run_batch_script(combined_commands)

        # self.run_command(isfile_or_dir_args(["icacls", path_str, "/setowner", "dummy_user"]))
        # self.run_command(isfile_or_dir_args(["icacls", path_str, "/deny", "dummy_user:(D,WDAC,WO)"]))
        # self.run_command(["cipher", "/e", path_str])

    @unittest.skip("skipped - requires admin permissions and overall an exhaustively involved test.")
    def test_gain_file_access(self):  # sourcery skip: extract-method
        test_file = Path("this file has no permissions.txt").absolute()
        try:
            with test_file.open("w", encoding="utf-8") as f:
                f.write("test")
        except PermissionError as e:
            ...
            # raise e
        self.remove_permissions(str(test_file))
        try:
            # Remove all permissions from the file

            test_filepath = Path(test_file)
            # self.assertFalse(os.access(test_file, os.W_OK), "Write access should be denied")  # this only checks attrs on windows
            # self.assertFalse(os.access(test_file, os.R_OK), "Read access should be denied")   # this only checks attrs on windows

            assert test_filepath.has_access(mode=1) == True  # this is a bug with os.access
            assert test_filepath.has_access(mode=7) == False

            assert test_filepath.gain_access(mode=6) == True
            assert test_filepath.has_access(mode=6) == True

            # self.assertFalse(os.access(test_file, os.R_OK), "Read access should be denied")   # this only checks attrs on windows
            # self.assertFalse(os.access(test_file, os.W_OK), "Write access should be denied")  # this only checks attrs on windows
        finally:
            # Clean up: Delete the temporary file
            # test_file.unlink()
            ...