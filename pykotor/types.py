from __future__ import annotations

from enum import IntEnum
from typing import overload, Union


class ResourceType:
    def __init__(self, id: int, extension: str, category: str):
        self.id: int = id
        self.category: str = category
        self.extension: str = extension

    def __eq__(self, other):
        if type(other) is str:
            return self.extension == other
        elif type(other) is int:
            return self.id == other
        elif type(other) is ResourceType:
            return self.extension == other.extension
        else:
            return False

    @staticmethod
    @overload
    def get(extension: str) -> ResourceType:
        ...

    @staticmethod
    @overload
    def get(resource_type: ResourceType) -> ResourceType:
        ...

    @staticmethod
    @overload
    def get(resource_id: int) -> ResourceType:
        ...

    @staticmethod
    def get(arg1: Union[str, int, ResourceType]) -> ResourceType:
        if type(arg1) is str:
            return resource_types[arg1]
        if type(arg1) is int:
            return resource_types[arg1]
        if type(arg1) is ResourceType:
            return arg1

    def __str__(self):
        return self.extension


class Language(IntEnum):
    English = 0


class Gender(IntEnum):
    Male = 0
    Female = 1


resource_types = {}
resource_types[""] = resource_types[0] = ResourceType(0, "", "Invalid")
resource_types["bmp"] = resource_types[1] = ResourceType(1, "bmp", "Images")
resource_types["tga"] = resource_types[3] = ResourceType(3, "tga", "Textures")
resource_types["wav"] = resource_types[4] = ResourceType(4, "wav", "Audio")
resource_types["plt"] = resource_types[6] = ResourceType(6, "plt", "Other")
resource_types["ini"] = resource_types[7] = ResourceType(7, "ini", "Other")
resource_types["txt"] = resource_types[10] = ResourceType(10, "txt", "Text")
resource_types["mdl"] = resource_types[2002] = ResourceType(2002, "mdl", "Models")
resource_types["nss"] = resource_types[2009] = ResourceType(2009, "nss", "Scripts")
resource_types["ncs"] = resource_types[2010] = ResourceType(2010, "ncs", "Scripts")
resource_types["mod"] = resource_types[2011] = ResourceType(2011, "mod", "Modules")
resource_types["are"] = resource_types[2012] = ResourceType(2012, "are", "Module Info")
resource_types["set"] = resource_types[2013] = ResourceType(2013, "set", "Module Info")
resource_types["ifo"] = resource_types[2014] = ResourceType(2014, "ifo", "Module Info")
resource_types["bic"] = resource_types[2015] = ResourceType(2015, "bic", "Creatures")
resource_types["wok"] = resource_types[2016] = ResourceType(2016, "wok", "Walkmeshes")
resource_types["2da"] = resource_types[2017] = ResourceType(2017, "2da", "2D Arrays")
resource_types["tlk"] = resource_types[2018] = ResourceType(2018, "tlk", "Talk Tables")
resource_types["txi"] = resource_types[2022] = ResourceType(2022, "txi", "Textures")
resource_types["git"] = resource_types[2023] = ResourceType(2023, "git", "Module Info")
resource_types["???"] = resource_types[2024] = ResourceType(2024, "bti", "Items")
resource_types["uti"] = resource_types[2025] = ResourceType(2025, "uti", "Items")
resource_types["btc"] = resource_types[2026] = ResourceType(2026, "btc", "Creatures")
resource_types["utc"] = resource_types[2027] = ResourceType(2027, "utc", "Creatures")
resource_types["dlg"] = resource_types[2029] = ResourceType(2029, "dlg", "Dialogs")
resource_types["itp"] = resource_types[2030] = ResourceType(2030, "itp", "Other")
resource_types["utt"] = resource_types[2032] = ResourceType(2032, "utt", "Triggers")
resource_types["dds"] = resource_types[2033] = ResourceType(2033, "dds", "Textures")
resource_types["uts"] = resource_types[2035] = ResourceType(2035, "uts", "Sounds")
resource_types["ltr"] = resource_types[2036] = ResourceType(2036, "ltr", "Other")
resource_types["gff"] = resource_types[2037] = ResourceType(2037, "gff", "Other")
resource_types["fac"] = resource_types[2038] = ResourceType(2038, "fac", "Factions")
resource_types["ute"] = resource_types[2040] = ResourceType(2040, "ute", "Encounters")
resource_types["utd"] = resource_types[2042] = ResourceType(2042, "utd", "Doors")
resource_types["utp"] = resource_types[2044] = ResourceType(2044, "utp", "Placeables")
resource_types["dft"] = resource_types[2045] = ResourceType(2045, "dft", "Other")
resource_types["gic"] = resource_types[2046] = ResourceType(2046, "gic", "Module Ifo")
resource_types["gui"] = resource_types[2047] = ResourceType(2047, "gui", "GUIs")
resource_types["utm"] = resource_types[2051] = ResourceType(2051, "utm", "Merchants")
resource_types["dwk"] = resource_types[2052] = ResourceType(2052, "dwk", "Walkmeshes")
resource_types["pwk"] = resource_types[2053] = ResourceType(2053, "pwk", "Walkmeshes")
resource_types["jrl"] = resource_types[2056] = ResourceType(2056, "jrl", "Journals")
resource_types["utw"] = resource_types[2058] = ResourceType(2058, "utw", "Waypoints")
resource_types["ssf"] = resource_types[2060] = ResourceType(2060, "ssf", "Soundsets")
resource_types["ndb"] = resource_types[2064] = ResourceType(2064, "ndb", "Other")
resource_types["ptm"] = resource_types[2065] = ResourceType(2065, "ptm", "Other")
resource_types["ptt"] = resource_types[2066] = ResourceType(2066, "ptt", "Other")
resource_types["jpg"] = resource_types[2076] = ResourceType(2076, "jpg", "Images")
resource_types["png"] = resource_types[2110] = ResourceType(2110, "png", "Images")
resource_types["lyt"] = resource_types[3000] = ResourceType(3000, "lyt", "Layouts")
resource_types["vis"] = resource_types[3001] = ResourceType(3001, "vis", "Layouts")
resource_types["rim"] = resource_types[3002] = ResourceType(3002, "rim", "Modules")
resource_types["pth"] = resource_types[3003] = ResourceType(3003, "pth", "Paths")
resource_types["lip"] = resource_types[3004] = ResourceType(3004, "lip", "Lips")
resource_types["tpc"] = resource_types[3007] = ResourceType(3007, "tpc", "Textures")
resource_types["mdx"] = resource_types[3008] = ResourceType(3008, "mdx", "Models")
resource_types["erf"] = resource_types[9997] = ResourceType(9997, "erf", "Modules")
resource_types["mp3"] = resource_types[25014] = ResourceType(25014, "mp3", "Audio")
