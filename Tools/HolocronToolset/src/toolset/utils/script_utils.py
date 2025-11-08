from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy.QtWidgets import QFileDialog, QMessageBox

from toolset.gui.widgets.settings.installations import GlobalSettings, NoConfigurationSetError

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
    from pykotor.tools.registry import SpoofKotorRegistry

log = RobustLogger()

NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG = (
    "PyKotor has detected you are using the {} version of nwnnsscomp.<br>"
    " This version doesn't have any known functional problems, though it DOES require that the registry"
    " key path:<br>{}<br>matches your KotOR installation path.<br><br>"
    "Your installation path ({}),<br>"
    "DOES NOT MATCH the registry value ({})<br><br>"
    "Due to the above, the compilation/decompilation will most likely fail.<br>"
    "Either restart HolocronToolset with admin privileges, or download and use the"
    " TSLPatcher version of nwnnsscomp to fix this issue.<br><br>"
    "Error details: {}"
)


class NoOpRegistrySpoofer:
    def __enter__(self) -> Self:
        log.debug("Enter NoOpRegistrySpoofer")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        log.debug(f"NoOpRegistrySpoofer.__exit__({exc_type}, {exc_val}, {exc_tb})")


def setup_extract_path() -> Path:
    """Sets up and returns the extraction path for temporary files.

    Returns:
    -------
        Path to the extraction directory.

    Raises:
    ------
        NoConfigurationSetError: If no valid temp directory is set or selected.
    """
    global_settings = GlobalSettings()
    extract_path = Path(global_settings.extractPath)

    if not extract_path.is_dir():
        extract_path_str: str | None = QFileDialog.getExistingDirectory(None, "Select a temp directory")
        extract_path: Path | None = Path(extract_path_str) if extract_path_str else None
        if extract_path is None or not extract_path.exists() or not extract_path.is_dir():
            msg: str = "Temp directory has not been set or is invalid."
            raise NoConfigurationSetError(msg)
    return extract_path


def handle_permission_error(
    reg_spoofer: SpoofKotorRegistry | NoOpRegistrySpoofer,
    extCompiler: ExternalNCSCompiler,
    installation_path: Path,
    e: PermissionError,
):
    """Handles permission errors that occur during registry spoofing operations.

    Args:
    ----
        reg_spoofer: The registry spoofer instance that encountered the error.
        extCompiler: The external compiler being used.
        installation_path: Path to the game installation.
        e: The permission error that occurred.

    Raises:
    ------
        PermissionError: If the error occurred with a NoOpRegistrySpoofer.
    """
    if isinstance(reg_spoofer, NoOpRegistrySpoofer):
        raise TypeError(str(e))

    # Spoofing was required but failed. Show the relevant message.
    msg: str = NON_TSLPATCHER_NWNNSSCOMP_PERMISSION_MSG.format(
        extCompiler.get_info().value.name,
        reg_spoofer.registry_path,
        installation_path,
        reg_spoofer.original_value,
        str(e),
    )
    log.warning(msg.replace("<br>", "\n"))
    longMsgBoxErr = QMessageBox(
        QMessageBox.Icon.Warning,
        "Permission denied when attempting to update nwnnsscomp in registry",
        msg,
    )
    longMsgBoxErr.setIcon(QMessageBox.Icon.Warning)
    longMsgBoxErr.exec()
