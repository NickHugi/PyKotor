import os.path
from typing import List

import concurrent.futures

from pykotor.common.stream import BinaryReader, BinaryWriter

from pykotor.extract.capsule import Capsule

from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.misc import is_capsule_file
from pykotor.tslpatcher.logger import PatchLogger


class InstallFile:
    def __init__(self, filename: str, replace_existing: bool) -> None:
        self.filename: str = filename
        self.replace_existing: bool = replace_existing

    def _identifier(self) -> ResourceIdentifier:
        return ResourceIdentifier.from_path(self.filename)

    def apply_encapsulated(
        self, log: PatchLogger, source_folder: str, destination: Capsule
    ) -> None:
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
            data = BinaryReader.load_file(f"{source_folder}/{self.filename}")
            destination.add(resname, restype, data)

    def apply_file(
        self, log: PatchLogger, source_folder: str, destination: str, local_folder: str
    ) -> None:
        data = BinaryReader.load_file(f"{source_folder}/{self.filename}")
        save_file_to = f"{destination}/{self.filename}"

        if self.replace_existing or not os.path.exists(save_file_to):
            if not os.path.exists(destination):
                log.add_note(f"Folder {destination} did not exist, creating it...")
                os.makedirs(destination)
            if self.replace_existing and not os.path.exists(save_file_to):
                log.add_note(f"Replacing file {self.filename} to the {local_folder} folder...")
            else:
                log.add_note(f"Copying file {self.filename} to the {local_folder} folder...")
            BinaryWriter.dump(save_file_to, data)
        elif not self.replace_existing and os.path.exists(save_file_to):
            log.add_warning(
                f"A file named {self.filename} already exists in the {local_folder} folder. Skipping file..."
            )

class InstallFolder:
# The `InstallFolder` class represents a folder that can be installed, and it provides a method to
# apply the installation by copying files from a source path to a destination path.
    def __init__(self, foldername: str, files: List[InstallFile] = None) -> None:
        self.foldername: str = foldername
        self.files: List[InstallFile] = [] if files is None else files

    def apply(self, log: PatchLogger, source_path: str, destination_path: str) -> None:
        """
        The function applies changes to files in a source directory and copies them to a destination
        directory using multithreading.

        :param log: The `log` parameter is an instance of the `PatchLogger` class. It is used to log any
        information or errors during the execution of the `apply` method
        :type log: PatchLogger
        :param source_path: The `source_path` parameter is a string that represents the path to the source
        directory or file. It is the location from where the files will be copied or applied
        :type source_path: str
        :param destination_path: The `destination_path` parameter is a string that represents the path where
        the files will be copied to. It specifies the directory where the files will be placed
        :type destination_path: str
        """
        if is_capsule_file(self.foldername):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self.apply_encapsulated_file, log, source_path, destination_path, file)
                    for file in self.files
                ]
                concurrent.futures.wait(futures)  # Wait for all threads to finish
        else:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        self.apply_file, log, source_path, destination_path, self.foldername, file
                    )
                    for file in self.files
                ]
                concurrent.futures.wait(futures)  # Wait for all threads to finish

    def apply_encapsulated_file(
        self, log: PatchLogger, source_path: str, destination_path: str, file: InstallFile
    ) -> None:
        """
        The function applies an encapsulated file to a destination path.

        :param log: A PatchLogger object that is used for logging information during the file
        application process
        :type log: PatchLogger
        :param source_path: The source path is the path to the file that needs to be installed or
        copied. It is the location of the file on the local machine or in the source directory
        :type source_path: str
        :param destination_path: The `destination_path` parameter is a string that represents the path
        where the file should be installed or copied to
        :type destination_path: str
        :param file: The `file` parameter is an instance of the `InstallFile` class
        :type file: InstallFile
        """

        target = f"{destination_path}/{self.foldername}"
        destination = Capsule(target, create_nonexisting=True)
        file.apply_encapsulated(log, source_path, destination)

    @staticmethod
    def apply_file(
        log: PatchLogger,
        source_path: str,
        destination_path: str,
        foldername: str,
        file: InstallFile,
    ) -> None:
        """
        The function `apply_file` applies a file to a specified destination path with a given folder
        name.

        :param log: A PatchLogger object that is used for logging information during the file
        application process
        :type log: PatchLogger
        :param source_path: The source path is the path to the file or folder that you want to copy or
        move. It can be an absolute path or a relative path from the current working directory
        :type source_path: str
        :param destination_path: The destination path is the directory where the file will be copied to
        :type destination_path: str
        :param foldername: The `foldername` parameter is a string that represents the name of the folder
        where the file will be applied
        :type foldername: str
        :param file: The `file` parameter is an instance of the `InstallFile` class
        :type file: InstallFile
        """
        target = f"{destination_path}/{foldername}"
        file.apply_file(log, source_path, target, foldername)
