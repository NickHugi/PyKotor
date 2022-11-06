import os.path
from configparser import ConfigParser
from typing import List, Dict

from pykotor.extract.capsule import Capsule

from pykotor.resource.formats.gff.gff_auto import bytes_gff

from pykotor.resource.formats.erf import read_erf, write_erf, ERF
from pykotor.common.stream import BinaryReader, BinaryWriter

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.formats.rim import read_rim, write_rim, RIM
from pykotor.resource.formats.ssf import read_ssf, write_ssf
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.mods.gff import ModificationsGFF
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.install import InstallFolder
from pykotor.tslpatcher.mods.ssf import ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA


class PatcherConfig:
    def __init__(self):
        self.install_list: List[InstallFolder] = []
        self.patches_2da: List[Modifications2DA] = []
        self.patches_gff: List[ModificationsGFF] = []
        self.patches_ssf: List[ModificationsSSF] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, append: TLK) -> None:
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        ConfigReader(ini, append).load(self)


class ModInstaller:
    def __init__(self, mod_path: str, game_path: str):
        self.game_path: str = game_path
        self.mod_path: str = mod_path
        self.output_path: str = game_path
        self.log: PatchLogger = PatchLogger()

    def install(self) -> None:
        append_tlk = read_tlk(self.mod_path + "/append.tlk")
        ini_text = BinaryReader.load_file(self.mod_path + "/changes.ini").decode()

        installation = Installation(self.game_path)
        memory = PatcherMemory()
        twodas = {}
        soundsets = {}
        templates = {}

        config = PatcherConfig()
        config.load(ini_text, append_tlk)

        # Apply changes to dialog.tlk
        dialog_tlk = read_tlk(installation.path() + "dialog.tlk")
        config.patches_tlk.apply(dialog_tlk, memory)
        write_tlk(dialog_tlk, self.output_path + "/dialog.tlk")

        for folder in config.install_list:
            folder.apply(self.log, self.mod_path, self.output_path)

        # Apply changes to 2DA files
        for patch in config.patches_2da:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            twoda = twodas[patch.filename] = read_2da(search.data)
            patch.apply(twoda, memory)
            write_2da(twoda, "{}/override/{}".format(self.output_path, patch.filename))

        # Apply changes to SSF files
        for patch in config.patches_ssf:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            soundset = soundsets[patch.filename] = read_ssf(search.data)
            patch.apply(soundset, memory)
            write_ssf(soundset, "{}/override/{}".format(self.output_path, patch.filename))

        # Apply changes to GFF files
        for patch in config.patches_gff:
            resname, restype = ResourceIdentifier.from_path(patch.filename)

            scan_capsules = []
            if patch.destination.endswith(".rim") or patch.destination.endswith(".erf") or patch.destination.endswith(".mod"):
                scan_capsules.append(Capsule(self.output_path + "/" + patch.destination))

            search = installation.resource(
                resname,
                restype,
                [SearchLocation.OVERRIDE, SearchLocation.CUSTOM_FOLDERS, SearchLocation.CUSTOM_MODULES, SearchLocation.CHITIN],
                folders=[self.mod_path],
                capsules=scan_capsules
            )

            template = templates[patch.filename] = read_gff(search.data)
            patch.apply(template, memory)
            self.write("{}/{}".format(self.output_path, patch.destination), patch.filename, bytes_gff(template))

    def write(self, filepath: str, filename: str, data: bytes) -> None:
        resname, restype = ResourceIdentifier.from_path(filename)
        if filepath.endswith(".rim"):
            rim = read_rim(BinaryReader.load_file(filepath)) if os.path.exists(filepath) else RIM()
            rim.set(resname, restype, data)
            write_rim(rim, filepath)
        elif filepath.endswith(".mod") or filepath.endswith(".erf"):
            erf = read_erf(BinaryReader.load_file(filepath)) if os.path.exists(filepath) else ERF()
            erf.set(resname, restype, data)
            write_erf(erf, filepath)
        else:
            BinaryWriter.dump(filepath, data)
