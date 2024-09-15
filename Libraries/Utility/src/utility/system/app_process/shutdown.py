from __future__ import annotations

import multiprocessing
import os
import shlex
import subprocess
import sys
import threading
import time

from loggerplus import RobustLogger

from utility.misc import is_frozen


def start_shutdown_process(main_pid: int | None = None):
    """Start a new process to monitor and shut down the main application.

    If the main process hangs or fails to exit cleanly, this process will forcefully
    terminate the main process and all its child processes.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(sys.path)
    startupinfo = None
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    else:
        main_pid = os.getpid() if main_pid is None else main_pid
        os.fork()
        shutdown_main_process(main_pid)
        return

    args = [sys.executable, "-c", f"from utility.system.app_process.shutdown import shutdown_main_process; shutdown_main_process({os.getpid()})"]
    if is_frozen():
        multiprocessing.Process(target=shutdown_main_process, args=(os.getpid(),))
    elif os.name == "nt":
        subprocess.Popen(  # noqa: S603
            args,  # noqa: S603
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
            start_new_session=True,
            env=env,
            startupinfo=startupinfo,
        )
    else:  # keep in case we end up needing to enable this logic later.
        subprocess.Popen(  # noqa: S603
            args,  # noqa: S603
            start_new_session=True,
            env=env,
            startupinfo=startupinfo,
        )


def shutdown_main_process(main_pid: int, *, timeout: int = 3):
    """Watchdog process to monitor and shut down the main application.

    If the main process hangs or fails to exit cleanly, this process will forcefully
    terminate the main process and all its child processes.
    """
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
    ignored_pids = [] if ignored_pids is None else ignored_pids
    RobustLogger().info("Attempting to terminate child processes gracefully...")

    active_children = multiprocessing.active_children()
    RobustLogger().debug("%s active child processes found", len(active_children))
    number_timeout_children = 0
    number_failed_children = 0
    for child in active_children:
        if child.pid in ignored_pids:
            RobustLogger().debug("Ignoring pid %s, found in ignore list.", child.pid)
            continue

        RobustLogger().debug("Politely ask child process %s to terminate", child.pid)
        try:
            child.terminate()
            RobustLogger().debug("Waiting for process %s to terminate with timeout of %s", child.pid, timeout)
            child.join(timeout)
        except multiprocessing.TimeoutError:
            number_timeout_children += 1
            RobustLogger().warning("Child process %s did not terminate in time. Forcefully terminating.", child.pid)
            try:
                if os.name == "nt":
                    from utility.system.os_helper import win_get_system32_dir

                    command = shlex.join([str(win_get_system32_dir() / "taskkill.exe"), "/F", "/T", "/PID", str(child.pid)])
                    subprocess.run(  # noqa: S603
                        shlex.split(command),
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=True,
                    )
                else:
                    import signal

                    os.kill(child.pid, signal.SIGKILL)  # Use SIGKILL as a last resort
            except Exception:  # noqa: BLE001
                number_failed_children += 1
                RobustLogger().critical("Failed to kill process %s", child.pid, exc_info=True)
    if number_failed_children:
        RobustLogger().error("Failed to terminate %s total processes!", number_failed_children)
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
    RobustLogger().debug("%s existing threads to terminate.", len(other_threads))
    if not other_threads:
        return True

    for thread in other_threads:
        if thread.__class__.__name__ == "_DummyThread":
            RobustLogger().debug("Ignoring dummy thread '%s'", thread.getName())
            continue
        if not thread.is_alive():
            RobustLogger().debug("Ignoring dead thread '%s'", thread.getName())
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
        RobustLogger().debug("All threads terminated gracefully; exiting normally.")
    return bool(number_timeout_threads)


def terminate_main_process(
    timeout: int = 3,
    actual_self_pid: int | None = None,
):
    """Waits for a specified timeout for threads to complete.

    If threads other than the main thread are still running after the timeout, it forcefully terminates
    the process. Otherwise, exits normally.
    """
    # Wait for the timeout period to give threads a chance to finish
    time.sleep(timeout)
    result1, result2 = True, True

    try:
        result1 = terminate_child_processes(timeout=timeout)
        if actual_self_pid is None:
            result2 = gracefully_shutdown_threads(timeout=timeout)
            actual_self_pid = os.getpid()
        if result1 and result2:
            RobustLogger().debug("Call sys.exit NOW")
            sys.exit(0)

        RobustLogger().warning("Child processes and/or threads did not terminate, killing main process %s as a fallback.", actual_self_pid)
        if os.name == "nt":
            from utility.system.os_helper import win_get_system32_dir

            sys32path = win_get_system32_dir()
            command = shlex.join([str(sys32path / "taskkill.exe"), "/F", "/T", "/PID", str(actual_self_pid)])
            subprocess.run(  # noqa: S603
                shlex.split(command),
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=True,
            )
        else:
            import signal

            os.kill(actual_self_pid, signal.SIGKILL)
    except Exception:  # noqa: BLE001
        RobustLogger().exception("Exception occurred while shutting down the main process")
    finally:
        RobustLogger().debug("call os.exit NOW")
        os._exit(0 if result1 and result2 else 1)


if __name__ == "__main__":
    def main():
        """Test the shutdown process."""
        start_shutdown_process()
        while True:
            time.sleep(1)

    main()
