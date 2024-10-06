from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qtpy import QtCore

from toolset.config import getRemoteToolsetUpdateInfo

if TYPE_CHECKING:
    from toolset.gui.windows.main import ToolWindow


class UpdateCheckThread(QtCore.QThread):
    """Thread for checking for updates."""

    update_info_fetched = QtCore.Signal(dict, dict, bool)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, tool_window: ToolWindow, *, silent: bool = False):
        super().__init__()
        self.tool_window: ToolWindow = tool_window
        self.silent: bool = silent

    def run(self):
        # This method is executed in a separate thread
        master_info, edge_info = self.get_latest_version_info()
        self.update_info_fetched.emit(master_info, edge_info, self.silent)

    def get_latest_version_info(self) -> tuple[dict[str, Any], dict[str, Any]]:
        edge_info: dict[str, Any] = {}
        if self.tool_window.settings.useBetaChannel:
            edge_info = self._get_remote_toolset_update_info(useBetaChannel=True)

        master_info: dict[str, Any] = self._get_remote_toolset_update_info(useBetaChannel=False)
        return master_info, edge_info

    def _get_remote_toolset_update_info(self, *, useBetaChannel: bool) -> dict[str, Any]:
        result: Exception | dict[str, Any] = getRemoteToolsetUpdateInfo(useBetaChannel=useBetaChannel, silent=self.silent)
        print(f"<SDM> [get_latest_version_info scope] {'edge_info' if useBetaChannel else 'master_info'}: ", result)

        if not isinstance(result, dict):
            if self.silent:
                result = {}
            elif isinstance(result, BaseException):
                raise result
            else:
                raise TypeError(f"Unexpected result type: {result}")

        return result