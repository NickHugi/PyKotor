from __future__ import annotations

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose


class SSFBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ssf: SSF | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> SSF:
        self._ssf = SSF()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "SSF ":
            msg = "Attempted to load an invalid SSF was loaded."
            raise ValueError(msg)

        if file_version != "V1.1":
            msg = "The supplied SSF file version is not supported."
            raise ValueError(msg)

        sounds_offset = self._reader.read_uint32()
        self._reader.seek(sounds_offset)

        self._ssf.set_data(SSFSound.BATTLE_CRY_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_4, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_5, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BATTLE_CRY_6, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.SELECT_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.ATTACK_GRUNT_3, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.PAIN_GRUNT_1, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.PAIN_GRUNT_2, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.LOW_HEALTH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.DEAD, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.CRITICAL_HIT, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.TARGET_IMMUNE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.LAY_MINE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.DISARM_MINE, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_STEALTH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_SEARCH, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.BEGIN_UNLOCK, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.UNLOCK_FAILED, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.UNLOCK_SUCCESS, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(
            SSFSound.SEPARATED_FROM_PARTY,
            self._reader.read_uint32(max_neg1=True),
        )
        self._ssf.set_data(SSFSound.REJOINED_PARTY, self._reader.read_uint32(max_neg1=True))
        self._ssf.set_data(SSFSound.POISONED, self._reader.read_uint32(max_neg1=True))

        return self._ssf


class SSFBinaryWriter(ResourceWriter):
    def __init__(
        self,
        ssf: SSF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._ssf: SSF = ssf

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
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
        self._writer.write_uint32(
            self._ssf.get(SSFSound.SEPARATED_FROM_PARTY),
            max_neg1=True,
        )
        self._writer.write_uint32(self._ssf.get(SSFSound.REJOINED_PARTY), max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.POISONED), max_neg1=True)

        for _i in range(12):
            self._writer.write_uint32(0xFFFFFFFF)
