from __future__ import annotations

from pykotor.resource.formats.ncs.ncs_data import (
    NCS,
    NCSByteCode,
    NCSInstruction,
    NCSInstructionType,
    NCSInstructionTypeValue,
)
from pykotor.resource.type import (
    SOURCE_TYPES,
    TARGET_TYPES,
    ResourceReader,
    ResourceWriter,
)

class NCSBinaryReader(ResourceReader):
    def __init__(
            self,
            source: SOURCE_TYPES,
            offset: int = 0,
            size: int = 0
    ):
        super().__init__(source, offset, size)
        self._ncs: NCS | None = None
        self._instructions: dict[int, NCSInstruction] = {}
        self._jumps: dict[NCSInstruction, int] = {}

    def load(
            self,
            auto_close: bool = True
    ) -> NCS:
        self._ncs = NCS()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "NCS ":
            raise TypeError("The file type that was loaded is invalid.")

        if file_version != "V1.0":
            raise TypeError("The NCS version that was loaded is not supported.")

        self._instructions = {}  # offset -> instruction

        self._reader.seek(13)
        while self._reader.remaining() > 0:
            offset = self._reader.position()
            self._instructions[offset] = self._read_instruction()

        for instruction, jumpToOffset in self._jumps.items():
            instruction.jump = self._instructions[jumpToOffset]

        self._ncs.instructions = list(self._instructions.values())
        
        if auto_close:
            self._reader.close()

        return self._ncs

    def _read_instruction(self) -> NCSInstruction:
        byte_code = NCSByteCode(self._reader.read_uint8())
        qualifier = self._reader.read_uint8()
        type_value = NCSInstructionTypeValue(byte_code, qualifier)

        instruction = NCSInstruction()
        instruction.ins_type = NCSInstructionType(type_value)

        if instruction.ins_type in [NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP,
                                    NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP]:
            instruction.args.extend([self._reader.read_int32(big=True),
                                     self._reader.read_uint16(big=True)])

        elif instruction.ins_type in [NCSInstructionType.CONSTI]:
            instruction.args.extend([self._reader.read_uint32(big=True)])

        elif instruction.ins_type in [NCSInstructionType.CONSTF]:
            instruction.args.extend([self._reader.read_single(big=True)])

        elif instruction.ins_type in [NCSInstructionType.CONSTS]:
            length = self._reader.read_uint16(big=True)
            instruction.args.extend([self._reader.read_string(length)])

        elif instruction.ins_type in [NCSInstructionType.CONSTO]:
            instruction.args.extend([self._reader.read_uint16(big=True)])

        elif instruction.ins_type in [NCSInstructionType.ACTION]:
            instruction.args.extend([self._reader.read_uint16(big=True), self._reader.read_uint8(big=True)])

        elif instruction.ins_type in [NCSInstructionType.MOVSP]:
            instruction.args.extend([self._reader.read_int32(big=True)])

        elif instruction.ins_type in [NCSInstructionType.JMP, NCSInstructionType.JSR,
                                      NCSInstructionType.JZ, NCSInstructionType.JNZ]:
            jumpOffset = self._reader.read_int32(big=True) + self._reader.position() - 6
            self._jumps[instruction] = jumpOffset

        elif instruction.ins_type in [NCSInstructionType.DESTRUCT]:
            instruction.args.extend([self._reader.read_uint16(big=True), self._reader.read_int16(big=True), self._reader.read_uint16(big=True)])

        elif instruction.ins_type in [NCSInstructionType.DECISP, NCSInstructionType.INCISP,
                                      NCSInstructionType.DECIBP, NCSInstructionType.INCIBP]:
            instruction.args.extend([self._reader.read_uint32(big=True)])

        elif instruction.ins_type in [NCSInstructionType.STORE_STATE]:
            instruction.args.extend([self._reader.read_uint32(big=True), self._reader.read_uint32(big=True)])

        elif instruction.ins_type in [NCSInstructionType.EQUALTT, NCSInstructionType.NEQUALTT]:
            instruction.args.extend([self._reader.read_uint16])

        elif instruction.ins_type in [NCSInstructionType.NOP, NCSInstructionType.RETN, NCSInstructionType.SAVEBP,
                                      NCSInstructionType.RESTOREBP, NCSInstructionType.ADDII, NCSInstructionType.RSADDI,
                                      NCSInstructionType.RSADDO, NCSInstructionType.NEGI, NCSInstructionType.RSADDS,
                                      NCSInstructionType.EQUALII]:
            ...

        else:
            raise Exception(f"Tried to read unsupported instruction '{instruction.ins_type.name}' to NCS")

        return instruction


class NCSBinaryWriter(ResourceWriter):
    def __init__(
            self,
            ncs: NCS,
            target: TARGET_TYPES
    ):
        super().__init__(target)
        self._ncs: NCS = ncs
        self._offsets: dict[NCSInstruction, int] = {}
        self._sizes: dict[NCSInstruction, int] = {}

    def write(
            self,
            auto_close: bool = True
    ) -> None:
        offset = 13
        for instruction in self._ncs.instructions:
            self._sizes[instruction] = self.determine_size(instruction)
            self._offsets[instruction] = offset
            offset += self._sizes[instruction]

        self._writer.write_string("NCS ")
        self._writer.write_string("V1.0")
        self._writer.write_uint8(0x42)
        self._writer.write_uint32(offset, big=True)

        for instruction in self._ncs.instructions:
            self._write_instruction(instruction)

        if auto_close:
            self._writer.close()

    def determine_size(self, instruction: NCSInstruction) -> int:
        size = 2

        if instruction.ins_type in [NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP,
                                    NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP]:
            size = 8

        elif instruction.ins_type in [NCSInstructionType.CONSTI]:
            size += 4

        elif instruction.ins_type in [NCSInstructionType.CONSTF]:
            size += 4

        elif instruction.ins_type in [NCSInstructionType.CONSTS]:
            size += 2 + len(instruction.args[0])

        elif instruction.ins_type in [NCSInstructionType.CONSTO]:
            size = 6

        elif instruction.ins_type in [NCSInstructionType.ACTION]:
            size = 5

        elif instruction.ins_type in [NCSInstructionType.MOVSP]:
            size += 4

        elif instruction.ins_type in [NCSInstructionType.JMP, NCSInstructionType.JSR,
                                      NCSInstructionType.JZ, NCSInstructionType.JNZ]:
            size += 4

        elif instruction.ins_type in [NCSInstructionType.DESTRUCT]:
            size += 6

        elif instruction.ins_type in [NCSInstructionType.DECISP, NCSInstructionType.INCISP,
                                      NCSInstructionType.DECIBP, NCSInstructionType.INCIBP]:
            size += 4

        elif instruction.ins_type in [NCSInstructionType.STORE_STATE]:
            size += 8

        elif instruction.ins_type in [NCSInstructionType.EQUALTT, NCSInstructionType.NEQUALTT]:
            size += 2

        elif instruction.ins_type in [NCSInstructionType.NOP]:
            ...

        else:
            ...

        return size

    def _write_instruction(self, instruction: NCSInstruction) -> None:
        self._writer.write_uint8(int(instruction.ins_type.value.byte_code))
        self._writer.write_uint8(int(instruction.ins_type.value.qualifier))

        if instruction.ins_type in [NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP,
                                    NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP]:
            self._writer.write_int32(instruction.args[0], big=True)
            self._writer.write_uint16(4, big=True)  # TODO: 12 for float support

        elif instruction.ins_type in [NCSInstructionType.CONSTI]:
            self._writer.write_int32(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.CONSTF]:
            self._writer.write_single(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.CONSTS]:
            self._writer.write_string(instruction.args[0], big=True, prefix_length=2)

        elif instruction.ins_type in [NCSInstructionType.CONSTO]:
            self._writer.write_uint32(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.ACTION]:
            self._writer.write_uint16(instruction.args[0], big=True)
            self._writer.write_uint8(instruction.args[1], big=True)

        elif instruction.ins_type in [NCSInstructionType.MOVSP]:
            self._writer.write_int32(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.JMP, NCSInstructionType.JSR,
                                      NCSInstructionType.JZ, NCSInstructionType.JNZ]:
            relative = self._offsets[instruction.jump] - self._offsets[instruction]
            self._writer.write_int32(relative, big=True)

        elif instruction.ins_type in [NCSInstructionType.DESTRUCT]:
            self._writer.write_uint16(instruction.args[0], big=True)
            self._writer.write_int16(instruction.args[1], big=True)
            self._writer.write_uint16(instruction.args[2], big=True)

        elif instruction.ins_type in [NCSInstructionType.DECISP, NCSInstructionType.INCISP,
                                      NCSInstructionType.DECIBP, NCSInstructionType.INCIBP]:
            self._writer.write_int32(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.STORE_STATE]:
            self._writer.write_uint32(instruction.args[0], big=True)
            self._writer.write_uint32(instruction.args[1], big=True)

        elif instruction.ins_type in [NCSInstructionType.EQUALTT, NCSInstructionType.NEQUALTT]:
            self._writer.write_uint16(instruction.args[0], big=True)

        elif instruction.ins_type in [NCSInstructionType.EQUALII, NCSInstructionType.EQUALFF,
                                      NCSInstructionType.EQUALFF, NCSInstructionType.EQUALOO,
                                      NCSInstructionType.EQUALEFFEFF, NCSInstructionType.EQUALEVTEVT,
                                      NCSInstructionType.EQUALEVTEVT, NCSInstructionType.EQUALLOCLOC,
                                      NCSInstructionType.EQUALTALTAL, NCSInstructionType.EQUALSS]:
            ...

        elif instruction.ins_type in [NCSInstructionType.NEQUALII, NCSInstructionType.NEQUALFF,
                                      NCSInstructionType.NEQUALFF, NCSInstructionType.NEQUALOO,
                                      NCSInstructionType.NEQUALEFFEFF, NCSInstructionType.NEQUALEVTEVT,
                                      NCSInstructionType.NEQUALEVTEVT, NCSInstructionType.NEQUALLOCLOC,
                                      NCSInstructionType.NEQUALTALTAL, NCSInstructionType.NEQUALSS]:
            ...

        elif instruction.ins_type in [NCSInstructionType.ADDII, NCSInstructionType.ADDFF,
                                      NCSInstructionType.ADDFI, NCSInstructionType.ADDIF,
                                      NCSInstructionType.ADDSS, NCSInstructionType.ADDVV]:
            ...

        elif instruction.ins_type in [NCSInstructionType.SUBII, NCSInstructionType.SUBFF,
                                      NCSInstructionType.SUBFI, NCSInstructionType.SUBIF,
                                      NCSInstructionType.SUBVV]:
            ...

        elif instruction.ins_type in [NCSInstructionType.MULII, NCSInstructionType.MULFF,
                                      NCSInstructionType.MULFI, NCSInstructionType.MULIF,
                                      NCSInstructionType.MULFV, NCSInstructionType.MULVF]:
            ...

        elif instruction.ins_type in [NCSInstructionType.DIVII, NCSInstructionType.DIVFF,
                                      NCSInstructionType.DIVFI, NCSInstructionType.DIVIF,
                                      NCSInstructionType.DIVFV, NCSInstructionType.DIVVF]:
            ...

        elif instruction.ins_type in [NCSInstructionType.GTII, NCSInstructionType.GTFF,
                                      NCSInstructionType.GEQII, NCSInstructionType.GEQFF]:
            ...

        elif instruction.ins_type in [NCSInstructionType.LTII, NCSInstructionType.LTFF,
                                      NCSInstructionType.LEQII, NCSInstructionType.LEQFF]:
            ...

        elif instruction.ins_type in [NCSInstructionType.LOGANDII, NCSInstructionType.LOGORII]:
            ...

        elif instruction.ins_type in [NCSInstructionType.BOOLANDII]:
            ...

        elif instruction.ins_type in [NCSInstructionType.INCORII]:
            ...

        elif instruction.ins_type in [NCSInstructionType.NEGI, NCSInstructionType.NEGF]:
            ...

        elif instruction.ins_type in [NCSInstructionType.MODII]:
            ...

        elif instruction.ins_type in [NCSInstructionType.NOTI]:
            ...

        elif instruction.ins_type in [NCSInstructionType.RETN]:
            ...

        elif instruction.ins_type in [NCSInstructionType.RSADDI, NCSInstructionType.RSADDF, NCSInstructionType.RSADDO,
                                      NCSInstructionType.RSADDS, NCSInstructionType.RSADDEFF, NCSInstructionType.RSADDEVT,
                                      NCSInstructionType.RSADDLOC, NCSInstructionType.RSADDTAL, NCSInstructionType.SAVEBP]:
            ...

        elif instruction.ins_type in [NCSInstructionType.NOP]:
            ...

        else:
            raise Exception(f"Tried to write unsupported instruction ({instruction.ins_type.name}) to NCS")

