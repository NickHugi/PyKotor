import os.path
from abc import ABC, abstractmethod
from typing import List

from pykotor.common.stream import BinaryReader, BinaryWriter

from pykotor.extract.file import ResourceIdentifier

from pykotor.extract.capsule import Capsule

from pykotor.resource.formats.erf import read_erf, write_erf, ERF
from pykotor.resource.formats.rim import read_rim, write_rim, RIM


class InstallFile:
    def __init__(self, filename: str, replace_existing: bool):
        self.filename: str = filename
        self.replace_existing: bool = replace_existing

    def _identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_path(self.filename)

    def apply_rim(self, source_folder: str, destination: RIM):
        resname, restype = self._identifier()

        if self.replace_existing or destination.get(resname, restype) is None:
            data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
            destination.set(resname, restype, data)

    def apply_erf(self, source_folder: str, destination: ERF):
        resname, restype = self._identifier()

        if self.replace_existing or destination.get(resname, restype) is None:
            data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
            destination.set(resname, restype, data)

    def apply_file(self, source_folder: str, destination: str):
        data = BinaryReader.load_file("{}/{}".format(source_folder, self.filename))
        save_file_to = "{}/{}".format(destination, self.filename)
        if self.replace_existing or not os.path.exists(save_file_to):
            if not os.path.exists(destination):
                os.makedirs(destination)
            BinaryWriter.dump(save_file_to, data)


class InstallFolder:
    def __init__(self, foldername: str, files: List[InstallFile] = None):
        self.foldername: str = foldername
        self.files: List[InstallFile] = [] if files is None else files

    def apply(self, source_path: str, destination_path: str):
        target = "{}/{}".format(destination_path, self.foldername)

        if self.foldername.endswith(".rim"):
            destination = read_rim(target) if os.path.exists(target) else RIM()
            [file.apply_rim(source_path, destination) for file in self.files]
            write_rim(destination, target)
        elif self.foldername.endswith(".mod"):
            destination = read_erf(target) if os.path.exists(target) else ERF()
            [file.apply_erf(source_path, destination) for file in self.files]
            write_erf(destination, target)
        else:
            [file.apply_file(source_path, target) for file in self.files]
