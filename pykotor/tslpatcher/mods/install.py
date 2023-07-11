from abc import ABC, abstractmethod
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
        return ResourceIdentifier.from_path(self.filename)

    def apply_encapsulated(self, log: PatchLogger, source_folder: str, destination: Capsule):
        resname, restype = self._identifier()

        if self.replace_existing or destination.resource(resname, restype) is None:
            if self.replace_existing and destination.resource(resname, restype) is not None:
                log.add_note("Replacing file {} in the {} archive...".format(self.filename, destination.filename()))
            else:
                log.add_note("Adding file {} in the {} archive...".format(self.filename, destination.filename()))

            data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
            destination.add(resname, restype, data)

    def apply_file(self, log: PatchLogger, source_folder: Path, destination: Path, local_folder: str):
        data = BinaryReader.load_file(source_folder / self.filename)
        save_file_to = destination / self.filename

        if self.replace_existing or not save_file_to.exists:
            if not destination.exists:
                log.add_note("Folder {} did not exist, creating it...".format(destination))
                destination.mkdir(parents=True)

            if self.replace_existing and not save_file_to.exists:
                log.add_note("Replacing file '{}' to the '{}' folder...".format(self.filename, local_folder))
            else:
                log.add_note("Copying file '{}' to the '{}' folder...".format(self.filename, local_folder))

            BinaryWriter.dump(save_file_to.resolve(), data)
        elif not self.replace_existing and save_file_to.exists:
            log.add_warning("A file named '{}' already exists in the '{}' folder. Skipping file...".format(self.filename, local_folder))


class InstallFolder:
    def __init__(self, foldername: str, files: List[InstallFile] = None):
        self.foldername: str = foldername
        self.files: List[InstallFile] = [] if files is None else files

    def apply(self, log: PatchLogger, source_path: Path, destination_path: Path):
        target = destination_path / self.foldername

        if is_capsule_file(self.foldername):
            destination = Capsule(target, create_nonexisting=True)
            [file.apply_encapsulated(log, source_path, destination) for file in self.files]
        else:
            [file.apply_file(log, source_path, target, self.foldername) for file in self.files]
