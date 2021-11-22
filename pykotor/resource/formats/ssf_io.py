from __future__ import annotations

import io
from typing import Optional
from xml.etree import ElementTree

from pykotor.common.stream import BinaryReader, BinaryWriter

import pykotor.resource.formats.ssf
from pykotor.resource.type import ResourceType


class SSFBinaryReader:
    def __init__(self, reader: BinaryReader):
        self._reader: BinaryReader = reader
        self._ssf: Optional[pykotor.resource.formats.ssf.SSF] = None
    
    def load(self) -> pykotor.resource.formats.ssf.SSF:
        from pykotor.resource.formats.ssf import SSFSound
        
        self._ssf = pykotor.resource.formats.ssf.SSF()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "SSF ":
            raise TypeError("Attempted to load an invalid SSF was loaded.")

        if file_version != "V1.1":
            raise TypeError("The supplied SSF file version is not supported.")

        sounds_offset = self._reader.read_uint32()
        self._reader.seek(sounds_offset)

        self._ssf.set(SSFSound.BATTLE_CRY_1, self._reader.read_uint32())
        self._ssf.set(SSFSound.BATTLE_CRY_2, self._reader.read_uint32())
        self._ssf.set(SSFSound.BATTLE_CRY_3, self._reader.read_uint32())
        self._ssf.set(SSFSound.BATTLE_CRY_4, self._reader.read_uint32())
        self._ssf.set(SSFSound.BATTLE_CRY_5, self._reader.read_uint32())
        self._ssf.set(SSFSound.BATTLE_CRY_6, self._reader.read_uint32())
        self._ssf.set(SSFSound.SELECT_1, self._reader.read_uint32())
        self._ssf.set(SSFSound.SELECT_2, self._reader.read_uint32())
        self._ssf.set(SSFSound.SELECT_3, self._reader.read_uint32())
        self._ssf.set(SSFSound.ATTACK_GRUNT_1, self._reader.read_uint32())
        self._ssf.set(SSFSound.ATTACK_GRUNT_2, self._reader.read_uint32())
        self._ssf.set(SSFSound.ATTACK_GRUNT_3, self._reader.read_uint32())
        self._ssf.set(SSFSound.PAIN_GRUNT_1, self._reader.read_uint32())
        self._ssf.set(SSFSound.PAIN_GRUNT_2, self._reader.read_uint32())
        self._ssf.set(SSFSound.LOW_HEALTH, self._reader.read_uint32())
        self._ssf.set(SSFSound.DEAD, self._reader.read_uint32())
        self._ssf.set(SSFSound.CRITICAL_HIT, self._reader.read_uint32())
        self._ssf.set(SSFSound.TARGET_IMMUNE, self._reader.read_uint32())
        self._ssf.set(SSFSound.LAY_MINE, self._reader.read_uint32())
        self._ssf.set(SSFSound.DISARM_MINE, self._reader.read_uint32())
        self._ssf.set(SSFSound.BEGIN_STEALTH, self._reader.read_uint32())
        self._ssf.set(SSFSound.BEGIN_SEARCH, self._reader.read_uint32())
        self._ssf.set(SSFSound.BEGIN_UNLOCK, self._reader.read_uint32())
        self._ssf.set(SSFSound.UNLOCK_FAILED, self._reader.read_uint32())
        self._ssf.set(SSFSound.UNLOCK_SUCCESS, self._reader.read_uint32())
        self._ssf.set(SSFSound.SEPARATED_FROM_PARTY, self._reader.read_uint32())
        self._ssf.set(SSFSound.REJOINED_PARTY, self._reader.read_uint32())
        self._ssf.set(SSFSound.POISONED, self._reader.read_uint32())
        
        return self._ssf


class SSFBinaryWriter:
    def __init__(self, writer: BinaryWriter, ssf: pykotor.resource.formats.ssf.SSF):
        self._writer: BinaryWriter = writer
        self._ssf = ssf

    def write(self) -> None:
        from pykotor.resource.formats.ssf import SSFSound

        self._writer.clear()

        self._writer.write_string("SSF ")
        self._writer.write_string("V1.1")
        self._writer.write_uint32(12)

        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_1), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_2), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_3), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_4), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_5), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_6), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_1), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_2), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_3), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_1), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_2), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_3), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_1), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_2), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LOW_HEALTH), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DEAD), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.CRITICAL_HIT), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.TARGET_IMMUNE), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LAY_MINE), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DISARM_MINE), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_STEALTH), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_SEARCH), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_UNLOCK), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_FAILED), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_SUCCESS), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SEPARATED_FROM_PARTY), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.REJOINED_PARTY), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.POISONED), max_neg1=True)

        for i in range(8):
            self._writer.write_uint32(0xFFFFFFFF)


class SSFXMLReader:
    def __init__(self, reader: BinaryReader):
        self._xml_root: ElementTree.Element = ElementTree.parse(io.StringIO(reader.read_all().decode())).getroot()
        self._ssf: Optional[pykotor.resource.formats.ssf.SSF] = None

    def load(self) -> pykotor.resource.formats.ssf.SSF:
        from pykotor.resource.formats.ssf import SSFSound

        self._ssf = pykotor.resource.formats.ssf.SSF()

        for child in self._xml_root.getroot():
            try:
                sound = SSFSound(int(child.attrib['id']))
                stringref = int(child.attrib['strref'])
                self._ssf.set(sound, stringref)
            except ValueError:
                pass

        return self._ssf
