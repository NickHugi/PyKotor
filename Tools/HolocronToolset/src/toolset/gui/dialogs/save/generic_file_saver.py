from __future__ import annotations

import shutil

from typing import TYPE_CHECKING, Generic, Sequence, TypeVar, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pykotor.extract.file import FileResource, ResourceResult
from pykotor.resource.formats.erf.erf_data import ERFResource
from pykotor.resource.formats.rim.rim_data import RIMResource
from utility.error_handling import universal_simplify_exception
from utility.logger_util import RobustRootLogger
from utility.system.path import Path

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
        self.resources: list[T] = resources

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
                data = self.get_resource_data(resource)
                with path.open("wb") as file:
                    file.write(data)
            except Exception as e:  # noqa: PERF203
                failed_extractions[path] = e
                del successfully_saved_paths[resource]
            else:
                RobustRootLogger.info(f"Saved {self.get_resource_ident(resource)} to '{path}'")

        if failed_extractions:
            self._handle_failed_extractions(failed_extractions)

        return successfully_saved_paths, failed_extractions

    def build_paths_to_write(self) -> dict[T, Path]:
        paths_to_write: dict[T, Path] = {}
        if len(self.resources) == 1:
            resource = self.resources[0]
            identifier = self.get_resource_ident(resource)
            dialog = QFileDialog(self.parent, "Save File", str(identifier), "Files (*.*)")
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setOption(QFileDialog.DontConfirmOverwrite)
            response = dialog.exec_()
            if response == QFileDialog.Accepted:
                filepath_str = dialog.selectedFiles()[0]
                if not filepath_str or not filepath_str.strip():
                    RobustRootLogger.debug("QFileDialog was accepted but no filepath str passed.")
                    return {}
                paths_to_write[resource] = Path(filepath_str)

        elif len(self.resources) > 1:
            folderpath_str: str = QFileDialog.getExistingDirectory(self.parent, "Extract to folder")
            if not folderpath_str or not folderpath_str.strip():
                RobustRootLogger.debug("User cancelled folderpath extraction.")
                return {}

            # Build intended destination filepaths dict
            folder_path = Path(folderpath_str)
            for resource in self.resources:
                identifier = self.get_resource_ident(resource)
                file_path = folder_path / str(identifier)
                paths_to_write[resource] = file_path

        else:
            RobustRootLogger.warning("FileSaveHandler: no resources sent with the constructor, nothing to save.")

        return paths_to_write

    def determine_save_paths(
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
            choice = self._prompt_existence_choice(existing_files_and_folders)

        # Build new_paths_to_write based on the choice.
        new_paths_to_write: dict[T, Path] = {}
        if choice == QMessageBox.StandardButton.Yes:
            RobustRootLogger.debug(
                "User chose to Overwrite %s files/folders in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )
            for resource, path in paths_to_write.items():
                is_overwrite = "overwriting existing file" if path.safe_isfile() else "saving as"
                RobustRootLogger.info("Extracting '%s' to '%s' and %s '%s'", path.name, path.parent, is_overwrite, path.name)
                try:
                    if path.safe_isdir():
                        shutil.rmtree(path)
                    elif path.safe_isfile():
                        path.unlink(missing_ok=True)
                except Exception as e:  # noqa: BLE001
                    if failed_extractions is not None:
                        failed_extractions[path] = e
                else:
                    new_paths_to_write[resource] = path
        elif choice == QMessageBox.StandardButton.No:
            RobustRootLogger.debug(
                "User chose to Rename %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )
            for resource, path in paths_to_write.items():
                new_path = path
                try:
                    i = 1
                    while new_path.safe_exists():
                        i += 1
                        new_path = new_path.with_stem(f"{path.stem} ({i})")
                except Exception as e:  # noqa: BLE001
                    if failed_extractions is not None:
                        failed_extractions[new_path] = e
                else:
                    if path.safe_isfile():
                        RobustRootLogger.info("Will save '%s' as '%s'", path.name, new_path)
                    new_paths_to_write[resource] = new_path
        else:
            RobustRootLogger.debug(
                "User chose to CANCEL overwrite/renaming of %s files in the '%s' folder.",
                len(existing_files_and_folders),
                next(iter(paths_to_write.values())).parent,
            )

        return new_paths_to_write

    def _prompt_existence_choice(
        self,
        existing_files_and_folders: list[str],
    ) -> int:
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle("Existing files/folders found.")
        msgBox.setText(f"The following {len(existing_files_and_folders)} files and folders already exist in the selected folder.<br><br>How would you like to handle this?")
        msgBox.setDetailedText("\n".join(existing_files_and_folders))
        msgBox.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Abort)
        msgBox.button(QMessageBox.StandardButton.Yes).setText("Overwrite")
        msgBox.button(QMessageBox.StandardButton.No).setText("Auto-Rename")
        msgBox.setDefaultButton(QMessageBox.StandardButton.Abort)
        msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
        return msgBox.exec_()

    def _handle_failed_extractions(
        self,
        failed_extractions: dict[Path, Exception],
    ):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Critical)
        msgBox.setWindowTitle("Failed to extract files to disk.")
        msgBox.setText(f"{len(failed_extractions)} files FAILED to to be saved<br><br>Press 'show details' for information.")
        detailed_info = "\n".join(
            f"{file}: {universal_simplify_exception(exc)}"
            for file, exc in failed_extractions.items()
        )
        msgBox.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint)
        msgBox.setDetailedText(detailed_info)
        msgBox.exec_()
