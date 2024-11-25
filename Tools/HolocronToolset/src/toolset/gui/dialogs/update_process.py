from __future__ import annotations

import gc
import multiprocessing
import sys

from multiprocessing import Queue
from typing import TYPE_CHECKING, Any, NoReturn

from loggerplus import RobustLogger
from qtpy.QtCore import QThread
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QStyle

from toolset.config import LOCAL_PROGRAM_INFO, toolset_tag_to_version, version_to_toolset_tag
from toolset.gui.dialogs.asyncloader import ProgressDialog
from utility.system.app_process.shutdown import terminate_child_processes
from utility.updater.update import AppUpdate

if TYPE_CHECKING:
    from utility.updater.github import GithubRelease


def run_progress_dialog(
    progress_queue: Queue,
    title: str = "Operation Progress",
) -> NoReturn:
    """Call this with multiprocessing.Process."""
    app = QApplication(sys.argv)
    dialog: ProgressDialog = ProgressDialog(progress_queue, title)
    icon: QIcon | None = app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)
    dialog.setWindowIcon(QIcon(icon))
    dialog.show()
    sys.exit(app.exec())


def start_update_process(
    release: GithubRelease,
    download_url: str,
) -> None:
    """Start the update process with progress dialog."""
    progress_queue: Queue = Queue()
    progress_process: multiprocessing.Process = multiprocessing.Process(
        target=run_progress_dialog,
        args=(
            progress_queue,
            "Holocron Toolset is updating and will restart shortly...",
        ),
    )
    progress_process.start()

    def download_progress_hook(
        data: dict[str, Any],
        progress_queue: Queue = progress_queue,
    ):
        progress_queue.put(data)

    def exitapp(kill_self_here: bool):  # noqa: FBT001
        packaged_data: dict[str, Any] = {"action": "shutdown", "data": {}}
        progress_queue.put(packaged_data)
        ProgressDialog.monitor_and_terminate(progress_process)
        gc.collect()
        for obj in gc.get_objects():
            if isinstance(obj, QThread) and obj.isRunning():
                RobustLogger().debug(f"Terminating QThread: {obj}")
                obj.terminate()
                obj.wait()
        terminate_child_processes()
        if kill_self_here:
            sys.exit(0)

    def expected_archive_filenames() -> list[str]:
        return [asset.name for asset in release.assets]

    updater = AppUpdate(
        [download_url],
        "HolocronToolset",
        LOCAL_PROGRAM_INFO["currentVersion"],
        toolset_tag_to_version(release.tag_name),
        downloader=None,
        progress_hooks=[download_progress_hook],
        exithook=exitapp,
        version_to_tag_parser=version_to_toolset_tag,
    )
    updater.get_archive_names = expected_archive_filenames

    try:
        progress_queue.put({"action": "update_status", "text": "Downloading update..."})
        updater.download(background=False)
        progress_queue.put({"action": "update_status", "text": "Restarting and Applying update..."})
        updater.extract_restart()
        progress_queue.put({"action": "update_status", "text": "Cleaning up..."})
        updater.cleanup()
    except Exception:  # noqa: BLE001
        RobustLogger().exception("Error occurred while downloading/installing the toolset.")
    finally:
        exitapp(kill_self_here=True)