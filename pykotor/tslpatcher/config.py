from pathlib import Path
from configparser import ConfigParser
from enum import IntEnum
from typing import List, Dict, Optional

from pykotor.extract.capsule import Capsule
from pykotor.resource.formats.erf.erf_data import ERFType

from pykotor.resource.formats.gff.gff_auto import bytes_gff

from pykotor.resource.formats.erf import read_erf, write_erf, ERF
from pykotor.common.stream import BinaryReader, BinaryWriter

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.formats.ncs.ncs_auto import bytes_ncs, compile_nss
from pykotor.resource.formats.rim import read_rim, write_rim, RIM
from pykotor.resource.formats.ssf import read_ssf, write_ssf
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tools.misc import is_capsule_file, is_mod_file, is_rim_file
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.mods.gff import ModificationsGFF
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFolder
from pykotor.tslpatcher.mods.nss import ModificationsNSS
from pykotor.tslpatcher.mods.ssf import ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA


class LogLevel(IntEnum):
    # Docstrings taken from ChangeEdit docs

    Nothing = 0
    """No feedback at all. The text from "info.rtf" will continue to be displayed during installation"""

    General = 1
    """Only general progress information will be displayed. Not recommended."""

    Errors = 2
    """General progress information is displayed, along with any serious errors encountered."""

    Warnings = 3
    """General progress information, serious errors and warnings are displayed. This is
    recommended for the release version of your mod."""

    Full = 4
    """Full feedback. On top of what is displayed at level 3, it also shows verbose progress
    information that may be useful for a Modder to see what is happening. Intended for
    Debugging."""


class PatcherConfig:
    def __init__(self):
        self.window_title: str = ""
        self.confirm_message: str = ""
        self.game_number: Optional[int] = None

        self.required_file: Optional[str] = None
        self.required_message: str = ""

        self.install_list: List[InstallFolder] = []
        self.patches_2da: List[Modifications2DA] = []
        self.patches_gff: List[ModificationsGFF] = []
        self.patches_ssf: List[ModificationsSSF] = []
        self.patches_nss: List[ModificationsNSS] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()
        self.patches_tlk_replace: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, append: TLK) -> None:
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        ConfigReader(ini, append).load(self)

    def patch_count(self) -> int:
        return len(self.patches_2da) + len(self.patches_gff) + len(self.patches_ssf) + 1 + len(self.install_list) + len(self.patches_nss)


class PatcherNamespace:
    def __init__(self):
        self.namespace_id: str = ""
        self.ini_filename: str = ""
        self.info_filename: str = ""
        self.data_folderpath: str = ""
        self.name: str = ""
        self.description: str = ""


class ModInstaller:
    def __init__(self, mod_path: Path, game_path: Path, ini_file: str, logger: PatchLogger = None):
        self.game_path: Path = game_path
        self.mod_path: Path = mod_path
        self.ini_file: str = ini_file
        self.output_path: Path = game_path
        self.log: PatchLogger = PatchLogger() if logger is None else logger

        self._config: Optional[PatcherConfig] = None

    def config(self) -> PatcherConfig:
        """
        Returns the PatcherConfig object associated with the mod installer. The object is created when the method is
        first called then cached for future calls.
        """

        if self._config is None:
            ini_text = BinaryReader.load_file(self.mod_path / self.ini_file).decode()

            self.log.add_note("Reading append.tlk")
            append_tlk_filepath = self.mod_path / "append.tlk"
            append_tlk = read_tlk(append_tlk_filepath) if append_tlk_filepath.exists() else TLK()

            self._config = PatcherConfig()
            self._config.load(ini_text, append_tlk)

        return self._config

    # extract into multiple funcs perhaps?
    def install(self) -> None:
        config = self.config()

        installation = Installation(self.game_path)
        memory = PatcherMemory()
        twodas = {}
        soundsets = {}
        templates = {}

        # Apply changes to dialog.tlk
        dialog_tlk = read_tlk(installation.path() / "dialog.tlk")
        config.patches_tlk.apply(dialog_tlk, memory)
        write_tlk(dialog_tlk, self.output_path / "dialog.tlk")
        self.log.complete_patch()

        for folder in config.install_list:
            folder.apply(self.log, self.mod_path, self.output_path)
            self.log.complete_patch()

        # Apply changes to 2DA files
        for patch in config.patches_2da:
            resname, restype = ResourceIdentifier.from_filename(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS], folders=[self.mod_path])
            twoda = twodas[patch.filename] = read_2da(search.data)

            self.log.add_note(f"Patching '{patch.name}'")
            patch.apply(twoda, memory)
            write_2da(twoda, self.output_path / "override" / patch.filename)

            self.log.complete_patch()

        # Apply changes to SSF files
        for patch in config.patches_ssf:
            resname, restype = ResourceIdentifier.from_filename(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS], folders=[self.mod_path])
            soundset = soundsets[patch.filename] = read_ssf(search.data)

            self.log.add_note(f"Patching '{patch.filename}'")
            patch.apply(soundset, memory)
            write_ssf(soundset, self.output_path / "override" / patch.filename)

            self.log.complete_patch()

        # Apply changes to GFF files
        for patch in config.patches_gff:
            resname, restype = ResourceIdentifier.from_filename(patch.filename)

            capsule = None
            gff_filepath = Path(self.output_path, patch.destination)
            if is_mod_file(patch.destination) or is_capsule_file(patch.destination):
                capsule = Capsule(gff_filepath)

            search = installation.resource(
                resname,
                restype,
                [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS, SearchLocation.CUSTOM_MODULES],
                folders=[self.mod_path],
                capsules=[] if capsule is None else [capsule]
            )

            norm_game_path = installation.path().resolve()
            norm_file_path = Path(patch.destination).resolve()
            local_path = str(norm_file_path).replace(str(norm_game_path), "")
            local_folder = local_path.replace(patch.filename, "")

            if capsule is None:
                self.log.add_note(f"Patching '{patch.filename}' in the '{local_folder}' folder.")
            else:
                self.log.add_note(f"Patching '{patch.filename}' in the '{local_path}' archive.")

            template = templates[patch.filename] = read_gff(search.data)
            patch.apply(template, memory, self.log)
            self.write(gff_filepath, patch.filename, bytes_gff(template), True)

            self.log.complete_patch()

        # Apply changes to NSS files
        for patch in config.patches_nss:
            capsule = None
            nss_output_filepath = Path(self.output_path, patch.destination)
            if is_capsule_file(patch.destination) or is_mod_file(patch.destination):
                capsule = Capsule(nss_output_filepath)

            nss_input_filepath = Path(self.mod_path, patch.filename)
            nss = [BinaryReader.load_file(nss_input_filepath).decode(errors="ignore")]

            norm_game_path = str(installation.path())
            norm_file_path = patch.destination
            local_path = str(norm_file_path).replace(norm_game_path, "")
            local_folder = local_path.replace(patch.filename, "")

            if capsule is None:
                self.log.add_note(f"Patching '{patch.filename}' in the '{local_folder}' folder.")
            else:
                self.log.add_note(f"Patching '{patch.filename}' in the '{local_path}' archive.")

            self.log.add_note(f"Compiling '{patch.filename}'")
            patch.apply(nss, memory, self.log)

            data = bytes_ncs(compile_nss(nss[0], installation.game()))
            file_name, ext = patch.filename.stem, patch.filename.suffix
            self.write(nss_output_filepath, file_name + ext.lower().replace(".nss", ".ncs"), data, patch.replace_file)

            self.log.complete_patch()

    def write(self, destination: Path, filename: str, data: bytes, replace: bool = False) -> None:
        resname, restype = ResourceIdentifier.from_filename(filename)
        file_extension = destination.suffix
        if is_rim_file(destination.name):
            rim = read_rim(BinaryReader.load_file(destination)) if destination.exists() else RIM()
            if not rim.get(resname, restype) or replace:
                rim.set(resname, restype, data)
                write_rim(rim, destination)
        elif is_mod_file(destination.name):
            erf = read_erf(BinaryReader.load_file(destination)) if destination.exists() else ERF(ERFType.from_extension(file_extension))
            if not erf.get(resname, restype) or replace:
                erf.set(resname, restype, data)
                write_erf(erf, destination)
        else:
            # TODO: fix later. Check if destination is already a filename with an extension. I've somehow encountered both scenarios.
            # a better solution would be finding out what caused this, as it definitely wasn't caused by a improper changes.ini
            filepath = destination if destination.suffix else Path(destination, filename)
            if not filepath.exists() or replace:
                BinaryWriter.dump(filepath, data)
