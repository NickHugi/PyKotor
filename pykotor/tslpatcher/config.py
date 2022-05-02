from typing import List

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.twoda import Modifications2DA


class PatcherConfig:
    def __init__(self, input_path: str, game_path: str):
        self.game_path: str = game_path
        self.input_path: str = input_path
        self.output_path: str = self.game_path
        self.installation: Installation = Installation(self.game_path)
        self.memory: PatcherMemory = PatcherMemory()
        self.patches_2da: List[Modifications2DA] = []

    def load(self) -> None:
        from pykotor.tslpatcher.reader import ConfigReader
        ConfigReader().load(self)

    def apply(self) -> None:
        twodas = {}

        for patch in self.patches_2da:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = self.installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            twoda = twodas[patch.filename] = read_2da(search.data)
            patch.apply(twoda, self.memory)
            write_2da(twoda, "{}/{}".format(self.installation.override_path(), patch.filename))
