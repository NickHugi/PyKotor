from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ssf.ssf_data import SSF, SSFSound
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class SSFBinaryReader(ResourceReader):
    """Reads SSF (Sound Set File) files.
    
    SSF files map sound event types to sound resource IDs. Used for creature sound sets
    that define battle cries, grunts, pain sounds, and other audio events.
    
    References:
    ----------
        vendor/reone/src/libs/resource/format/ssfreader.cpp:26-32 (SSF reading)
        vendor/reone/src/libs/resource/format/ssfwriter.cpp (SSF writing)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ssf: SSF | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> SSF:  # noqa: FBT001, FBT002, ARG002
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

        # vendor/reone/src/libs/resource/format/ssfreader.cpp:28-31
        # Read sound set entries (uint32 array, -1 indicates no sound)
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
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        self._writer.write_string("SSF ")
        self._writer.write_string("V1.1")
        self._writer.write_uint32(12)

        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_4) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_5) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BATTLE_CRY_6) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SELECT_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.ATTACK_GRUNT_3) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_1) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.PAIN_GRUNT_2) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LOW_HEALTH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DEAD) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.CRITICAL_HIT) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.TARGET_IMMUNE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.LAY_MINE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.DISARM_MINE) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_STEALTH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_SEARCH) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.BEGIN_UNLOCK) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_FAILED) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.UNLOCK_SUCCESS) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.SEPARATED_FROM_PARTY) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.REJOINED_PARTY) or 0, max_neg1=True)
        self._writer.write_uint32(self._ssf.get(SSFSound.POISONED) or 0, max_neg1=True)

        for _ in range(12):
            self._writer.write_uint32(0xFFFFFFFF)
