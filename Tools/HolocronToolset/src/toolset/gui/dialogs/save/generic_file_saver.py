from __future__ import annotations

import shutil

from pathlib import Path
from typing import TYPE_CHECKING, Generic, Literal, Sequence, TypeVar, Union

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pykotor.extract.file import FileResource, ResourceIdentifier, ResourceResult
from pykotor.resource.formats.erf.erf_data import ERFResource
from pykotor.resource.formats.rim.rim_data import RIMResource
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.extract.file import ResourceIdentifier


T = TypeVar(
    "T",
    bound=Union[FileResource, ERFResource, RIMResource, ResourceResult],
)


class FileSaveHandler(Generic[T]):
    def __init__(
        self,
        resources: Sequence[T],
        parent: QWidget | None = None,
    ):
        self.parent: QWidget | None = parent
        self.resources: list[T] = list(resources)

    def get_resource_data(
        self,
        resource: T,
    ) -> bytes:
        return resource.data() if isinstance(resource, FileResource) else resource.data

    def get_resource_ident(
        self,
        resource: T,
    ) -> ResourceIdentifier:
        return resource.identifier()

    def save_files(
        self,
        paths_to_write: dict[T, Path] | None = None,
    ) -> dict[T, Path]:
        """Processes self.resources and returns the paths that were saved successfully and a dict[Path, Exception] for ones that failed."""
        failed_extractions: dict[Path, Exception] = {}
        if paths_to_write is None:
            paths_to_write = self.build_paths_to_write()
        successfully_saved_paths: dict[T, Path] = self.determine_save_paths(paths_to_write, failed_extractions)

        for resource, path in successfully_saved_paths.items():
            try:
                data: bytes = self.get_resource_data(resource)
                with path.open("wb") as file:
                    file.write(data)
            except Exception as e:  # noqa: PERF203, BLE001
                failed_extractions[path] = e
                del successfully_saved_paths[resource]
            else:
                RobustLogger().info(f"Saved {self.get_resource_ident(resource)} to '{path}'")

        if failed_extractions:
            self._handle_failed_extractions(failed_extractions)

        return successfully_saved_paths

    def build_paths_to_write(self) -> dict[T, Path]:
        paths_to_write: dict[T, Path] = {}
        if len(self.resources) == 1:
            resource: T = self.resources[0]
            identifier = self.get_resource_ident(resource)
            from toolset.gui.common.localization import translate as tr
            dialog = QFileDialog(self.parent, tr("Save File"), str(identifier), "Files (*.*)")
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)  # pyright: ignore[reportArgumentType]
            dialog.setOption(QFileDialog.Option.DontConfirmOverwrite)  # pyright: ignore[reportArgumentType]
            response: int = dialog.exec()
            if response == QFileDialog.DialogCode.Accepted:
                filepath_str: str = dialog.selectedFiles()[0]
                if not filepath_str or not filepath_str.strip():
                    RobustLogger().debug("QFileDialog was accepted but no filepath str passed.")
                    return {}
                paths_to_write[resource] = Path(filepath_str)

        elif len(self.resources) > 1:
            folderpath_str: str = QFileDialog.getExistingDirectory(self.parent, "Extract to folder")
            if not folderpath_str or not folderpath_str.strip():
                RobustLogger().debug("User cancelled folderpath extraction.")
                return {}

            # Build intended destination filepaths dict
            folder_path = Path(folderpath_str)
            for resource in self.resources:
                identifier: ResourceIdentifier = self.get_resource_ident(resource)
                file_path: Path = folder_path / str(identifier)
                paths_to_write[resource] = file_path

        else:
            RobustLogger().warning("FileSaveHandler: no resources sent with the constructor, nothing to save.")

        return paths_to_write

    def determine_save_paths(  # noqa: C901, PLR0912
        self,
        paths_to_write: dict[T, Path],
        failed_extractions: dict[Path, Exception] | None = None,
    ) -> dict[T, Path]:
        """Determine the save paths for the given resources and prompt the user for any necessary actions regarding existing files.

        Args:
        ----
            - self (FileSaveHandler): The FileSaveHandler object.
            - failed_extractions (dict[Path, Exception] | None): A dictionary to store any failed extractions and their corresponding exceptions. Defaults to None.

        Returns:
        -------
            - paths_to_write (dict[T, Path]): A dictionary containing the paths to write for each resource.

        Processing Logic:
        ----------------
            - Prompt the user for a save location if only one resource is provided.
            - Prompt the user for a folder to extract to if multiple resources are provided.
            - Check for any existing files or folders in the intended save location.
            - Prompt the user for an action to take regarding existing files/folders.
            - Build a new dictionary of paths to write based on the user's choice.
        """
        if not paths_to_write:
            return {}

        # Build existing paths
        existing_files_and_folders: list[str] = []
        for path in paths_to_write.values():
            if path.exists():
                file_relpath = str(path.relative_to(path.parents[1] if path.parent.parent.name else path.parent))
                existing_files_and_folders.append(file_relpath)

        # Determine the action to take regarding existing files/folders.
        if not existing_files_and_folders:
            choice = QMessageBox.StandardButton.No  # Default to rename, useful when not executing the save immediately.
        else:
            choice: int = self._prompt_existence_choice(existing_files_and_folders)

        # Build new_paths_to_write based on the choice.
        new_paths_to_write: dict[T, Path] = {}
        if choice == QMessageBox.StandardButton.Yes:
            RobustLogger().debug(
                "User chose to Overwrite %s files/folders in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )
            for resource, path in paths_to_write.items():
                is_overwrite: Literal["overwriting existing file", "saving as"] = "overwriting existing file" if path.is_file() else "saving as"
                RobustLogger().info("Extracting '%s' to '%s' and %s '%s'", path.name, path.parent, is_overwrite, path.name)
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    elif path.is_file():
                        path.unlink(missing_ok=True)
                except Exception as e:  # noqa: BLE001
                    if failed_extractions is not None:
                        failed_extractions[path] = e
                else:
                    new_paths_to_write[resource] = path
        elif choice == QMessageBox.StandardButton.No:
            RobustLogger().debug(
                "User chose to Rename %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )
            for resource, path in paths_to_write.items():
                new_path = path
                try:
                    i = 1
                    while new_path.exists():
                        i += 1
                        new_path: Path = path.parent / f"{path.stem} ({i}){path.suffix}"
                except Exception as e:  # noqa: BLE001
                    if failed_extractions is not None:
                        failed_extractions[new_path] = e
                else:
                    if path.is_file():
                        RobustLogger().info("Will save '%s' as '%s'", path.name, new_path)
                    new_paths_to_write[resource] = new_path
        else:
            RobustLogger().debug(
                "User chose to CANCEL overwrite/renaming of %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )

        return new_paths_to_write

    def _prompt_existence_choice(
        self,
        existing_files_and_folders: list[str],
    ) -> int:
        from toolset.gui.common.localization import translate as tr, trf
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(tr("Existing files/folders found."))
        msg_box.setText(trf("The following {count} files and folders already exist in the selected folder.<br><br>How would you like to handle this?", count=len(existing_files_and_folders)))
        msg_box.setDetailedText("\n".join(existing_files_and_folders))
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Abort)  # pyright: ignore[reportArgumentType]
        yes_button, no_button = msg_box.button(QMessageBox.StandardButton.Yes), msg_box.button(QMessageBox.StandardButton.No)
        assert yes_button is not None, "Did not call setStandardButtons with the QMessageBox yes button."
        assert no_button is not None, "Did not call setStandardButtons with the QMessageBox yes button."
        yes_button.setText(tr("Overwrite"))
        no_button.setText(tr("Auto-Rename"))
        msg_box.setDefaultButton(QMessageBox.StandardButton.Abort)
        msg_box.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)  # pyright: ignore[reportArgumentType]
        return msg_box.exec()

    def _handle_failed_extractions(
        self,
        failed_extractions: dict[Path, Exception],
    ):
        from toolset.gui.common.localization import translate as tr, trf
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(tr("Failed to extract files to disk."))
        msg_box.setText(trf("{count} files FAILED to to be saved<br><br>Press 'show details' for information.", count=len(failed_extractions)))
        detailed_info = "\n".join(f"{file}: {universal_simplify_exception(exc)}" for file, exc in failed_extractions.items())
        msg_box.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)  # pyright: ignore[reportArgumentType]
        msg_box.setDetailedText(detailed_info)
        msg_box.exec()
