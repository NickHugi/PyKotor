from pathlib import Path
from typing import List

from pykotor.common.stream import BinaryReader, BinaryWriter

from pykotor.extract.file import ResourceIdentifier

from pykotor.extract.capsule import Capsule

from pykotor.tools.misc import is_capsule_file
from pykotor.tslpatcher.logger import PatchLogger


class InstallFile:
    def __init__(self, filename: str, replace_existing: bool):
        self.filename: str = filename
        self.replace_existing: bool = replace_existing

    def _identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_filename(self.filename)

    def apply_encapsulated(self, log: PatchLogger, source_folder: str, destination: Capsule):
        resname, restype = self._identifier()

        if self.replace_existing or destination.resource(resname, restype) is None:
            if self.replace_existing and destination.resource(resname, restype) is not None:
                log.add_note(
                    f"Replacing file {self.filename} in the {destination.filename()} archive..."
                )
            else:
                log.add_note(
                    f"Adding file {self.filename} in the {destination.filename()} archive..."
                )

            data = BinaryReader.load_file(Path(source_folder) / self.filename)
            destination.add(resname, restype, data)

    def apply_file(self, log: PatchLogger, source_folder: Path, destination: Path, local_folder: str):
        data = BinaryReader.load_file(source_folder / self.filename)
        save_file_to = destination / self.filename

        if self.replace_existing or not save_file_to.exists():
            if not destination.exists():
                log.add_note(f"Folder {destination} did not exist, creating it...")
                destination.mkdir(parents=True)

            if self.replace_existing and not save_file_to.exists():
                log.add_note(
                    f"Replacing file '{self.filename}' to the '{local_folder}' folder..."
                )
            else:
                log.add_note(
                    f"Copying file '{self.filename}' to the '{local_folder}' folder..."
                )

            BinaryWriter.dump(save_file_to.resolve(), data)
        else:
            log.add_warning(
                f"A file named '{self.filename}' already exists in the '{local_folder}' folder. Skipping file..."
            )


class InstallFolder:
    def __init__(self, foldername: str, files: List[InstallFile] = None):
        self.foldername: str = foldername
        self.files: List[InstallFile] = [] if files is None else files

    def apply(self, log: PatchLogger, source_path: Path, destination_path: Path):
        target = destination_path / self.foldername

        if is_capsule_file(self.foldername):
            destination = Capsule(target, create_nonexisting=True)
            [file.apply_encapsulated(log, str(source_path.resolve()), destination) for file in self.files]
        else:
            [file.apply_file(log, source_path, target, self.foldername) for file in self.files]
