from __future__ import annotations

import asyncio
import cProfile
import os
import pstats
import sys
from datetime import datetime
from pathlib import Path

from contextlib import suppress

from loggerplus import RobustLogger
from qtpy.QtCore import QThread
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMessageBox

import resources_rc  # noqa: PLC0415, F401  # pylint: disable=ungrouped-imports,unused-import

from toolset.config import CURRENT_VERSION
from toolset.gui.windows.main import ToolWindow
from toolset.main_init import is_frozen, is_running_from_temp
from toolset.main_settings import setup_post_init_settings, setup_pre_init_settings, setup_toolset_default_env
from toolset.utils.window import TOOLSET_WINDOWS
from utility.system.app_process.shutdown import terminate_child_processes


def qt_cleanup():
    """Cleanup so we can exit."""
    RobustLogger().debug("Closing/destroy all windows from TOOLSET_WINDOWS list, (%s to handle)...", len(TOOLSET_WINDOWS))
    for window in TOOLSET_WINDOWS:
        window.close()
        window.destroy()

    TOOLSET_WINDOWS.clear()
    terminate_child_processes()


def _should_enable_profiling() -> bool:
    """Check if profiling should be enabled.
    
    Profiling is enabled by default when:
    - Not frozen (running from source)
    
    Profiling can be disabled by:
    - Setting environment variable TOOLSET_DISABLE_PROFILE to "1" or "true"
    - OR using --no-profile command-line argument
    
    Returns:
        bool: True if profiling should be enabled, False otherwise
    """
    # Never enable profiling in frozen builds
    if is_frozen():
        return False
    
    # Check if profiling is explicitly disabled
    env_disable = os.environ.get("TOOLSET_DISABLE_PROFILE", "").lower().strip()
    if env_disable in ("1", "true", "yes", "on"):
        return False
    
    # Check command-line argument to disable
    if "--no-profile" in sys.argv:
        return False
    
    # Enable by default when not frozen
    return True


def _save_profile_stats(profiler: cProfile.Profile, output_path: Path):
    """Save profiling statistics to files.
    
    Saves both:
    - Binary .prof file (for tools like snakeviz, py-spy, etc.)
    - Text .txt file (human-readable stats)
    
    Args:
        profiler: The cProfile.Profile instance
        output_path: Base path where to save the profile stats (will add .prof and .txt extensions)
    """
    try:
        # Save binary profile data (.prof) - compatible with snakeviz, py-spy, etc.
        profiler.dump_stats(str(output_path))
        
        # Also save human-readable text stats
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            stats = pstats.Stats(profiler, stream=f)
            stats.sort_stats("cumulative")
            stats.print_stats()
        
        RobustLogger().info("Profile statistics saved:")
        RobustLogger().info(f"  - Binary: {output_path} (use with snakeviz: snakeviz {output_path})")
        RobustLogger().info(f"  - Text: {txt_path} (human-readable)")
    except Exception as e:
        RobustLogger().error(f"Failed to save profile statistics: {e}")


def main():
    """Main entry point for the Holocron Toolset.

    This block is ran when users run __main__.py directly.
    
    When not frozen, cProfile is enabled by default to profile the application execution.
    Profile statistics will be saved to a timestamped file in the current directory.
    Profiling can be disabled by setting TOOLSET_DISABLE_PROFILE=1 or using --no-profile flag.
    """
    setup_pre_init_settings()
    
    # Enable profiling if requested and not frozen
    enable_profiling = _should_enable_profiling()
    profiler: cProfile.Profile | None = None
    profile_output_path: Path | None = None
    
    if enable_profiling:
        profiler = cProfile.Profile()
        profiler.enable()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_output_path = Path(f"toolset_profile_{timestamp}.prof")
        RobustLogger().info(f"Profiling enabled (default for non-frozen builds). Statistics will be saved to: {profile_output_path}")
        RobustLogger().info("To disable profiling, set TOOLSET_DISABLE_PROFILE=1 or use --no-profile flag")
        RobustLogger().info("Profiling will capture all function calls and execution times")

    app = QApplication(sys.argv)
    app.setApplicationName("HolocronToolset")
    app.setOrganizationName("PyKotor")
    app.setOrganizationDomain("github.com/NickHugi/PyKotor")
    app.setApplicationVersion(CURRENT_VERSION)
    app.setDesktopFileName("com.pykotor.toolset")
    app.setApplicationDisplayName("Holocron Toolset")
    icon_path = ":/images/icons/sith.png"
    icon = QIcon(icon_path)
    if icon.isNull():
        RobustLogger().warning(f"Warning: Main application icon not found at '{icon_path}'")
    else:
        app.setWindowIcon(icon)
    main_gui_thread: QThread | None = app.thread()
    assert main_gui_thread is not None, "Main GUI thread should not be None"
    main_gui_thread.setPriority(QThread.Priority.HighestPriority)
    
    def cleanup_with_profiling():
        """Cleanup function that also saves profiling stats if enabled."""
        # Disable profiler before cleanup to avoid profiling cleanup code
        if profiler is not None:
            profiler.disable()
        
        qt_cleanup()
        
        # Save profile stats after cleanup
        if profiler is not None and profile_output_path is not None:
            _save_profile_stats(profiler, profile_output_path)
    
    app.aboutToQuit.connect(cleanup_with_profiling)

    setup_post_init_settings()
    setup_toolset_default_env()

    if is_running_from_temp():
        QMessageBox.critical(
            None,
            "Error",
            "This application cannot be run from within a zip or temporary directory. Please extract it to a permanent location before running."
        )
        sys.exit("Exiting: Application was run from a temporary or zip directory.")

    tool_window = ToolWindow()
    tool_window.show()
    tool_window.update_manager.check_for_updates(silent=True)
    with suppress(ImportError):
        from qasync import QEventLoop  # type: ignore[import-not-found] # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
        asyncio.set_event_loop(QEventLoop(app))
    sys.exit(app.exec())
