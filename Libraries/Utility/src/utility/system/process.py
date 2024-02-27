from __future__ import annotations

import ctypes
import subprocess


def is_admin() -> bool:
    try:  # sourcery skip: do-not-use-bare-except
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:  # noqa: E722
        return False


def execute_process(program, args, use_shell_execute: bool, hide_process) -> tuple[int, bytes, bytes]:
    stdout_option: int | None = subprocess.PIPE if hide_process else None
    stderr_option: int | None = subprocess.PIPE if hide_process else None

    result: subprocess.CompletedProcess[bytes] = subprocess.run(
        [program, *args],
        shell=use_shell_execute,  # noqa: S603
        stdout=stdout_option,
        stderr=stderr_option,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr
