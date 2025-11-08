#!/usr/bin/env python3
from __future__ import annotations

import cProfile
import datetime
import gc
import os
import pathlib
import sys

from contextlib import suppress
from typing import TYPE_CHECKING

from toolset.main_init import is_running_from_temp, main_init

if TYPE_CHECKING:
    from qtpy.QtWidgets import QApplication


def qt_cleanup():
    """Cleanup so we can exit."""
    from loggerplus import RobustLogger
    from qtpy import QtCore

    from toolset.utils.window import TOOLSET_WINDOWS
    from utility.system.app_process.shutdown import terminate_child_processes  # pyright: ignore[reportMissingTypeStubs]

    RobustLogger().debug("Closing/destroy all windows from TOOLSET_WINDOWS list, (%s to handle)...", len(TOOLSET_WINDOWS))
    for window in TOOLSET_WINDOWS:
        window.close()
        window.destroy()
    TOOLSET_WINDOWS.clear()
    gc.collect()
    qt_thread_type = getattr(QtCore, "QThread", None)
    for obj in gc.get_objects():
        with suppress(RuntimeError):  # wrapped C/C++ object of type QThread has been deleted
            if qt_thread_type is not None and isinstance(obj, qt_thread_type) and obj.isRunning():
                RobustLogger().info(f"Terminating QThread: {obj}")
                obj.terminate()
                obj.wait()
    terminate_child_processes()


def setupPreInitSettings():
    from qtpy.QtWidgets import QApplication

    from toolset.gui.widgets.settings.widgets.application import ApplicationSettings

    # Some application settings must be set before the app starts.
    # These ones are accessible through the in-app settings window widget.
    settings_widget = ApplicationSettings()
    environment_variables: dict[str, str] = settings_widget.app_env_variables
    for key, value in environment_variables.items():
        os.environ[key] = os.environ.get(key, value)  # Use os.environ.get to prioritize the existing env.
    for attr_name, attr_value in settings_widget.REQUIRES_RESTART.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        QApplication.setAttribute(attr_value, settings_widget.settings.value(attr_name, QApplication.testAttribute(attr_value), bool))


def setupPostInitSettings(app: QApplication):
    from qtpy.QtGui import QFont
    from qtpy.QtWidgets import QApplication

    from toolset.gui.widgets.settings.widgets.application import ApplicationSettings
    settings_widget = ApplicationSettings()
    toolset_qsettings = settings_widget.settings
    app.setFont(toolset_qsettings.value("GlobalFont", app.font(), QFont))

    for attr_name, attr_value in settings_widget.__dict__.items():
        if attr_value is None:  # attr not available in this qt version.
            continue
        if attr_name.startswith("AA_"):
            QApplication.setAttribute(attr_value, toolset_qsettings.value(attr_name, QApplication.testAttribute(attr_value), bool))

    for name, setting in settings_widget.MISC_SETTINGS.items():
        if toolset_qsettings.contains(name):
            qsetting_lookup_val = toolset_qsettings.value(name, setting.getter(), setting.setting_type)
            setting.setter(qsetting_lookup_val)


def setupToolsetDefaultEnv():
    from toolset.main_init import is_frozen
    from utility.misc import is_debug_mode

    if os.name == "nt":
        os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = os.environ.get("QT_MULTIMEDIA_PREFERRED_PLUGINS", "windowsmediafoundation")
    if not is_debug_mode() or is_frozen():
        os.environ["QT_DEBUG_PLUGINS"] = os.environ.get("QT_DEBUG_PLUGINS", "0")
        os.environ["QT_LOGGING_RULES"] = os.environ.get("QT_LOGGING_RULES", "qt5ct.debug=false")  # Disable specific Qt debug output


def should_profile_with_debugpy() -> bool:
    debugpy_env = any(
        os.environ.get(var) for var in ("DEBUGPY_LAUNCHER_PORT", "DEBUGPY_PORT", "DEBUGPY_LISTEN")
    )
    if debugpy_env:
        return True

    debugpy_module = sys.modules.get("debugpy")
    if debugpy_module is not None:
        is_client_connected = getattr(debugpy_module, "is_client_connected", None)
        if callable(is_client_connected):
            try:
                return bool(is_client_connected())
            except Exception:
                return True
        return True
    return False


def dump_profile_stats(profile: cProfile.Profile) -> pathlib.Path:
    logs_dir = pathlib.Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    stats_path = logs_dir / f"debugpy_profile_{timestamp}.prof"
    profile.dump_stats(str(stats_path))
    return stats_path


def run_toolset():
    main_init()

    from qtpy import QtCore
    from qtpy.QtGui import QSurfaceFormat
    from qtpy.QtWidgets import QApplication, QMessageBox

    setupPreInitSettings()

    # Set default OpenGL surface format before creating QApplication
    # This is critical for PyPy and ensures proper OpenGL context initialization
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setVersion(3, 3)  # Request OpenGL 3.3
    # Use CompatibilityProfile instead of CoreProfile - CoreProfile requires VAO to be bound
    # before any buffer operations, which causes issues with PyOpenGL's lazy loading
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
    fmt.setSamples(4)  # Enable multisampling for antialiasing
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    app.setApplicationName("HolocronToolsetV3")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/NickHugi/PyKotor")
    qt_thread_type = getattr(QtCore, "QThread", None)
    if qt_thread_type is not None:
        app.thread().setPriority(qt_thread_type.Priority.HighestPriority)  # pyright: ignore[reportOptionalMemberAccess]
    app.aboutToQuit.connect(qt_cleanup)

    setupPostInitSettings(app)
    setupToolsetDefaultEnv()

    if is_running_from_temp():
        # Show error message using PyQt5's QMessageBox
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setWindowTitle("Error")
        msgBox.setText("This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running.")
        msgBox.exec_()  # pyright: ignore[reportAttributeAccessIssue]
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    from toolset.gui.windows.main import ToolWindow

    toolWindow = ToolWindow()
    toolWindow.show()
    toolWindow.checkForUpdates(silent=True)
    app.exec_()  # pyright: ignore[reportAttributeAccessIssue]


def main():
    if should_profile_with_debugpy():
        profiler = cProfile.Profile()
        try:
            profiler.enable()
            run_toolset()
        finally:
            profiler.disable()
            stats_path = dump_profile_stats(profiler)
            print(f"cProfile stats written to {stats_path}")
    else:
        run_toolset()


if __name__ == "__main__":
    main()
