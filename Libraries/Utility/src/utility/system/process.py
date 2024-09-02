from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

from typing import Iterable


def execute_process(
    program: str,
    args: Iterable[str],
    *,
    use_shell_execute: bool,
    hide_process: bool,
) -> tuple[int, bytes, bytes]:
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


def is_frozen() -> bool:
    return (
        getattr(sys, "frozen", False)
        or getattr(sys, "_MEIPASS", False)
        # or tempfile.gettempdir() in sys.executable  # Not sure any frozen implementations use this (PyInstaller/py2exe). Re-enable if we find one that does.
    )


def start_shutdown_process():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    # Setup to hide the console window on Windows
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        main_pid = os.getpid()
        os.fork()
        shutdown_main_process(main_pid)
        return

    if is_frozen():
        import multiprocessing
        multiprocessing.Process(target=shutdown_main_process, args=(os.getpid(),))
    elif os.name == "nt":
        subprocess.Popen(
            [sys.executable, "-c", f"from utility.system.process import shutdown_main_process; shutdown_main_process({os.getpid()})"],  # noqa: S603
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW, start_new_session=True, env=env, startupinfo=startupinfo
        )
    else:  # keep in case we end up needing to enable this logic later.
        subprocess.Popen(
            [sys.executable, "-c", f"from utility.system.process import shutdown_main_process; shutdown_main_process({os.getpid()})"],  # noqa: S603
            start_new_session=True, env=env, startupinfo=startupinfo
        )


def shutdown_main_process(main_pid: int, *, timeout: int = 3):
    """Watchdog process to monitor and shut down the main application."""
    try:
        print(f"Waiting {timeout} second(s) before starting the shutdown failsafe.")
        time.sleep(timeout)
        print("Perform the shutdown/cleanup sequence")
        terminate_main_process(timeout, main_pid)
    except Exception:  # noqa: BLE001
        from loggerplus import RobustLogger
        RobustLogger().exception("Shutdown process encountered an exception!")


def terminate_child_processes(
    timeout: int = 3,
    ignored_pids: list[int] | None = None,
) -> bool:
    """Attempt to gracefully terminate and join all child processes of the given PID with a timeout.

    Forcefully terminate any child processes that do not terminate within the timeout period.
    """
    import multiprocessing

    from loggerplus import RobustLogger

    ignored_pids = [] if ignored_pids is None else ignored_pids
    log = RobustLogger()
    log.info("Attempting to terminate child processes gracefully...")

    active_children = multiprocessing.active_children()
    log.debug("%s active child processes found", len(active_children))
    number_timeout_children = 0
    number_failed_children = 0
    for child in active_children:
        if child.pid in ignored_pids:
            log.debug("Ignoring pid %s, found in ignore list.", child.pid)
            continue

        log.debug("Politely ask child process %s to terminate", child.pid)
        try:
            child.terminate()
            log.debug("Waiting for process %s to terminate with timeout of %s", child.pid, timeout)
            child.join(timeout)
        except multiprocessing.TimeoutError:
            number_timeout_children += 1
            log.warning("Child process %s did not terminate in time. Forcefully terminating.", child.pid)
            try:
                if os.name == "nt":
                    from utility.system.os_helper import win_get_system32_dir
                    subprocess.run([str(win_get_system32_dir() / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)],  # noqa: S603
                                   creationflags=subprocess.CREATE_NO_WINDOW, check=True)
                else:
                    import signal
                    os.kill(child.pid, signal.SIGKILL)  # Use SIGKILL as a last resort
            except Exception:  # noqa: BLE001
                number_failed_children += 1
                log.critical("Failed to kill process %s", child.pid, exc_info=True)
    if number_failed_children:
        log.error("Failed to terminate %s total processes!", number_failed_children)
    return bool(number_failed_children)


def gracefully_shutdown_threads(timeout: int = 3) -> bool:
    """Attempts to gracefully join all threads in the main process with a specified timeout.

    If any thread does not terminate within the timeout, record the error and proceed to terminate the next thread.
    After attempting with all threads, if any have timed out, force shutdown the process.

    If all terminate gracefully or if there are no threads, exit normally.
    """
    from loggerplus import RobustLogger
    RobustLogger().info("Attempting to terminate threads gracefully...")
    main_thread = threading.main_thread()
    other_threads = [t for t in threading.enumerate() if t is not main_thread]
    number_timeout_threads = 0
    print(f"{len(other_threads)} existing threads to terminate.")
    if not other_threads:
        return True

    for thread in other_threads:
        if thread.__class__.__name__ == "_DummyThread":
            print(f"Ignoring dummy thread '{thread.getName()}'")
            continue
        if not thread.is_alive():
            print(f"Ignoring dead thread '{thread.getName()}'")
            continue
        try:
            thread.join(timeout)
            if thread.is_alive():
                RobustLogger().warning("Thread '%s' did not terminate within the timeout period of %s seconds.", thread.name, timeout)
                number_timeout_threads += 1
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Failed to stop the thread")

    if number_timeout_threads:
        RobustLogger().warning("%s total threads would not terminate on their own!", number_timeout_threads)
    else:
        print("All threads terminated gracefully; exiting normally.")
    return bool(number_timeout_threads)


def terminate_main_process(
    timeout: int = 3,
    actual_self_pid: int | None = None,
):
    """Waits for a specified timeout for threads to complete.

    If threads other than the main thread are still running after the timeout, it forcefully terminates
    the process. Otherwise, exits normally.
    """
    from loggerplus import RobustLogger

    # Wait for the timeout period to give threads a chance to finish
    time.sleep(timeout)
    result1, result2 = True, True

    try:
        result1 = terminate_child_processes(timeout=timeout)
        if actual_self_pid is None:
            result2 = gracefully_shutdown_threads(timeout=timeout)
            actual_self_pid = os.getpid()
        if result1 and result2:
            print("Call sys.exit NOW")
            sys.exit(0)

        RobustLogger().warning("Child processes and/or threads did not terminate, killing main process %s as a fallback.", actual_self_pid)
        if os.name == "nt":
            from utility.system.os_helper import win_get_system32_dir
            sys32path = win_get_system32_dir()
            subprocess.run(
                [str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(actual_self_pid)],  # noqa: S603
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
        else:
            import signal
            os.kill(actual_self_pid, signal.SIGKILL)
    except Exception:  # noqa: BLE001
        RobustLogger().exception("Exception occurred while shutting down the main process")
    finally:
        print("call os.exit NOW")
        os._exit(0 if result1 and result2 else 1)
