import os.path
from abc import ABC, abstractmethod
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
                log.add_note("Replacing file {} in the {} archive...".format(self.filename, destination.path()))
            else:
                log.add_note("Adding file {} in the {} archive...".format(self.filename, destination.path()))

            data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
            destination.add(resname, restype, data)

    def apply_file(self, log: PatchLogger, source_folder: str, destination: str):
        data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
        save_file_to = "{}/{}".format(destination, self.filename)

        if self.replace_existing or not os.path.exists(save_file_to):
            if not os.path.exists(destination):
                log.add_note("Folder {} did not exist, creating it...".format(destination))
                os.makedirs(destination)

            if self.replace_existing and not os.path.exists(save_file_to):
                log.add_note("Replacing file {} to the {} folder...".format(self.filename, destination))
            else:
                log.add_note("Copying file {} to the {} folder...".format(self.filename, destination))

            BinaryWriter.dump(save_file_to, data)
        elif not self.replace_existing and os.path.exists(save_file_to):
            log.add_warning("A file named {} already exists in the {} folder. Skipping file...".format(self.filename, destination))


class InstallFolder:
    def __init__(self, foldername: str, files: List[InstallFile] = None):
        self.foldername: str = foldername
        self.files: List[InstallFile] = [] if files is None else files

    def apply(self, log: PatchLogger, source_path: str, destination_path: str):
        target = "{}/{}".format(destination_path, self.foldername)

        if is_capsule_file(self.foldername):
            destination = Capsule(target, create_nonexisting=True)
            [file.apply_encapsulated(log, source_path, destination) for file in self.files]
        else:
            [file.apply_file(log, source_path, target) for file in self.files]
