from __future__ import annotations

import shlex
import subprocess
import sys

from typing import Iterable, Mapping


def run_subprocess(
    program: str,
    args: Iterable[str],
    *,
    use_shell_execute: bool,
    hide_process: bool,
    timeout: int | None = None,
    creationflags: int = 0,
    env: Mapping[str, str] | None = None,
    check: bool = True,
    encoding: str = "utf-8",
    stdout_option: int | None = None,
    stderr_option: int | None = None,
) -> tuple[int, bytes, bytes]:
    stdout_option = subprocess.PIPE if hide_process else subprocess.DEVNULL
    stderr_option = subprocess.PIPE if hide_process else subprocess.DEVNULL
    escaped_args = [shlex.quote(arg) for arg in args]
    result: subprocess.CompletedProcess[bytes] = subprocess.run(  # noqa: S603
        [program, *escaped_args],
        shell=use_shell_execute,  # noqa: S603
        stdout=stdout_option,
        stderr=stderr_option,
        check=check,
        timeout=timeout,
        creationflags=creationflags,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
    )
