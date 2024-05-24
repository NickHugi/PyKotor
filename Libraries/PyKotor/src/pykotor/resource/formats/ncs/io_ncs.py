from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.ncs_data import NCS, NCSByteCode, NCSInstruction, NCSInstructionType, NCSInstructionTypeValue
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class NCSBinaryReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ncs: NCS | None = None
        self._instructions: dict[int, NCSInstruction] = {}
        self._jumps: dict[NCSInstruction, int] = {}

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> NCS:
        """Loads an NCS file from the reader.

        Args:
        ----
            auto_close: {Whether to automatically close the reader after loading}.

        Returns:
        -------
            NCS: The loaded NCS object

        Raises:
            ValueError - Corrupt NCS.
            OSError - some operating system issue occurred.

        Processing Logic:
        ----------------
            - Reads the file type and version headers
            - Reads each instruction from the file into a dictionary
            - Resolves jump offsets to reference the target instructions
            - Adds the instructions to the NCS object
            - Optionally closes the reader.
        """
        self._ncs = NCS()

        file_type = self._reader.read_string(4)
        file_version = self._reader.read_string(4)

        if file_type != "NCS ":
            msg = "The file type that was loaded is invalid."
            raise ValueError(msg)

        if file_version != "V1.0":
            msg = "The NCS version that was loaded is not supported."
            raise ValueError(msg)

        self._instructions = {}  # offset -> instruction

        self._reader.seek(13)
        while self._reader.remaining() > 0:
            offset = self._reader.position()
            self._instructions[offset] = self._read_instruction()

        for instruction, jumpToOffset in self._jumps.items():
            instruction.jump = self._instructions[jumpToOffset]

        self._ncs.instructions = list(self._instructions.values())

        return self._ncs

    def _read_instruction(self) -> NCSInstruction:
        """Reads an instruction from the bytecode reader.

        Args:
        ----
            self: {The class instance}: Provides access to the bytecode reader

        Returns:
        -------
            instruction: {An NCSInstruction object}: The instruction read from the bytecode

        Processing Logic:
        ----------------
            - Reads the byte code and qualifier from the reader
            - Determines the instruction type from these values
            - Initializes an NCSInstruction object
            - Reads arguments from the reader based on the instruction type
            - Handles jump offsets
            - Returns the completed instruction
        """
        byte_code = NCSByteCode(self._reader.read_uint8())
        qualifier = self._reader.read_uint8()
        type_value = NCSInstructionTypeValue(byte_code, qualifier)

        instruction = NCSInstruction()
        instruction.ins_type = NCSInstructionType(type_value)

        if instruction.ins_type in {
            NCSInstructionType.CPDOWNSP,
            NCSInstructionType.CPTOPSP,
            NCSInstructionType.CPDOWNBP,
            NCSInstructionType.CPTOPBP,
        }:
            instruction.args.extend([self._reader.read_int32(big=True), self._reader.read_uint16(big=True)])

        elif instruction.ins_type == NCSInstructionType.CONSTI:
            instruction.args.extend([self._reader.read_uint32(big=True)])

        elif instruction.ins_type == NCSInstructionType.CONSTF:
            instruction.args.extend([self._reader.read_single(big=True)])

        elif instruction.ins_type == NCSInstructionType.CONSTS:
            length = self._reader.read_uint16(big=True)
            instruction.args.extend([self._reader.read_string(length)])

        elif instruction.ins_type == NCSInstructionType.CONSTO:
            instruction.args.extend([self._reader.read_uint16(big=True)])

        elif instruction.ins_type == NCSInstructionType.ACTION:
            instruction.args.extend([self._reader.read_uint16(big=True), self._reader.read_uint8(big=True)])

        elif instruction.ins_type == NCSInstructionType.MOVSP:
            instruction.args.extend([self._reader.read_int32(big=True)])

        elif instruction.ins_type in {
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
        }:
            jumpOffset = self._reader.read_int32(big=True) + self._reader.position() - 6
            self._jumps[instruction] = jumpOffset

        elif instruction.ins_type == NCSInstructionType.DESTRUCT:
            instruction.args.extend(
                [
                    self._reader.read_uint16(big=True),
                    self._reader.read_int16(big=True),
                    self._reader.read_uint16(big=True),
                ],
            )

        elif instruction.ins_type in {
            NCSInstructionType.DECISP,
            NCSInstructionType.INCISP,
            NCSInstructionType.DECIBP,
            NCSInstructionType.INCIBP,
        }:
            instruction.args.extend([self._reader.read_uint32(big=True)])

        elif instruction.ins_type == NCSInstructionType.STORE_STATE:
            instruction.args.extend([self._reader.read_uint32(big=True), self._reader.read_uint32(big=True)])

        elif instruction.ins_type in {
            NCSInstructionType.EQUALTT,
            NCSInstructionType.NEQUALTT,
        }:
            instruction.args.extend([self._reader.read_uint16])

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.LOGANDII,
            NCSInstructionType.LOGORII,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.INCORII,
            NCSInstructionType.EXCORII,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.BOOLANDII:  # noqa: SIM114
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.EQUALII,
            NCSInstructionType.EQUALFF,
            NCSInstructionType.EQUALOO,
            NCSInstructionType.EQUALEFFEFF,
            NCSInstructionType.EQUALEVTEVT,
            NCSInstructionType.EQUALLOCLOC,
            NCSInstructionType.EQUALTALTAL,
            NCSInstructionType.EQUALSS,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.NEQUALII,
            NCSInstructionType.NEQUALFF,
            NCSInstructionType.NEQUALOO,
            NCSInstructionType.NEQUALEFFEFF,
            NCSInstructionType.NEQUALEVTEVT,
            NCSInstructionType.NEQUALLOCLOC,
            NCSInstructionType.NEQUALTALTAL,
            NCSInstructionType.NEQUALSS,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.GEQxx,
            NCSInstructionType.GEQII,
            NCSInstructionType.GEQFF,
            # NCSInstructionType.GTxx,
            NCSInstructionType.GTII,
            NCSInstructionType.GTFF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.LTxx,
            NCSInstructionType.LTII,
            NCSInstructionType.LTFF,
            # NCSInstructionType.LExx,
            NCSInstructionType.LEQII,
            NCSInstructionType.LEQFF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.SHLEFTII,
            NCSInstructionType.SHRIGHTII,
            NCSInstructionType.USHRIGHTII,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.ADDII,
            NCSInstructionType.ADDFF,
            NCSInstructionType.ADDFI,
            NCSInstructionType.ADDIF,
            NCSInstructionType.ADDSS,
            NCSInstructionType.ADDVV,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.SUBII,
            NCSInstructionType.SUBFF,
            NCSInstructionType.SUBFI,
            NCSInstructionType.SUBIF,
            NCSInstructionType.SUBVV,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.MULII,
            NCSInstructionType.MULFF,
            NCSInstructionType.MULFI,
            NCSInstructionType.MULIF,
            NCSInstructionType.MULFV,
            NCSInstructionType.MULVF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.DIVII,
            NCSInstructionType.DIVFF,
            NCSInstructionType.DIVFI,
            NCSInstructionType.DIVIF,
            NCSInstructionType.DIVFV,
            NCSInstructionType.DIVVF,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.MODII:  # noqa: SIM114
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.NEGx,
            NCSInstructionType.NEGI,
            NCSInstructionType.NEGF,
        }:
            ...

        elif (
            instruction.ins_type == NCSInstructionType.COMPI
            or instruction.ins_type
            in {  # noqa: SIM114
                # NCSInstructionType.STORE_STATEALL,
            }
        ):
            ...

        elif instruction.ins_type == NCSInstructionType.RETN:  # noqa: SIM114
            ...

        elif instruction.ins_type == NCSInstructionType.NOTI:  # noqa: SIM114
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.SAVEBP,
            NCSInstructionType.RESTOREBP,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.NOP:  # noqa: SIM114
            ...

        elif instruction.ins_type in {
            NCSInstructionType.RSADDI,
            NCSInstructionType.RSADDF,
            NCSInstructionType.RSADDO,
            NCSInstructionType.RSADDS,
            NCSInstructionType.RSADDEFF,  # ???
            NCSInstructionType.RSADDEVT,  # ???
            NCSInstructionType.RSADDLOC,  # ???
            NCSInstructionType.RSADDTAL,  # ???
        }:
            ...

        else:
            msg = f"Tried to read unsupported instruction '{instruction.ins_type.name}' to NCS"
            raise ValueError(msg)

        return instruction


class NCSBinaryWriter(ResourceWriter):
    def __init__(
        self,
        ncs: NCS,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._ncs: NCS = ncs
        self._offsets: dict[NCSInstruction, int] = {}
        self._sizes: dict[NCSInstruction, int] = {}

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ):
        """Writes the NCS file.

        Args:
        ----
            auto_close (bool): Whether to automatically close the writer.

        Processing Logic:
        ----------------
            - Calculates offset and size for each instruction
            - Writes header with file type and total size
            - Writes each instruction using pre-calculated offset and size
            - Closes writer if auto_close is True.
        """
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

    def determine_size(self, instruction: NCSInstruction) -> int:  # TODO
        """Determines the size of an NCS instruction. This function is unfinished and is missing defs.

        Args:
        ----
            instruction: NCSInstruction - The instruction to determine size for

        Returns:
        -------
            int - The size of the instruction in bytes
        """
        size = 2  # Base size for opcode and type

        if instruction.ins_type in {
            NCSInstructionType.CPDOWNSP,
            NCSInstructionType.CPTOPSP,
            NCSInstructionType.CPDOWNBP,
            NCSInstructionType.CPTOPBP,
            NCSInstructionType.DESTRUCT,
        }:
            size += 6

        elif instruction.ins_type == NCSInstructionType.STORE_STATE:
            size += 8

        elif instruction.ins_type in {
            NCSInstructionType.NEQUALTT,
            NCSInstructionType.EQUALTT,
        }:
            size += 2

        elif instruction.ins_type in {
            NCSInstructionType.MOVSP,
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
        }:
            size += 4  # 4 bytes for the value/offset, total 6 bytes

        elif instruction.ins_type in {
            NCSInstructionType.DECISP,
            NCSInstructionType.INCISP,
            NCSInstructionType.DECIBP,
            NCSInstructionType.INCIBP,
        }:
            size += 4

        elif instruction.ins_type in {
            NCSInstructionType.CONSTI,
            NCSInstructionType.CONSTF,
            NCSInstructionType.CONSTO,
        }:
            size += 4  # 4 bytes for the constant value/object ID, total 6 bytes

        elif instruction.ins_type == NCSInstructionType.CONSTS:
            size += 2 + len(instruction.args[0])  # 2 bytes for string length, plus string characters

        elif instruction.ins_type == NCSInstructionType.ACTION:
            size += 3  # 1 byte for argument count, 2 bytes for the routine number, total 5

        return size

    def _write_instruction(self, instruction: NCSInstruction):  # TODO
        """Writes an instruction to the NCS binary stream. This function is unfinished and is missing defs.

        Args:
        ----
            instruction (NCSInstruction): The instruction to write

        Processing Logic:
        ----------------
            - Writes instruction type and qualifier bytes
            - Writes instruction arguments based on type
                - Integer, float, string, object ID
                - Relative jump offsets
            - Raises error for unsupported instructions
        """

        def to_signed_32bit(n):  # FIXME: Presumably this issue happens further up the call stack, fix later.
            # Assuming n is provided as an unsigned 32-bit integer
            # Convert it to a signed 32-bit integer
            if n >= 2**31:
                n -= 2**32
            return n

        def to_signed_16bit(n):  # FIXME: Only seen this issue happen with 32bit but better safe than sorry, remove this once above issue is fixed.
            if n >= 2**15:
                n -= 2**16
            return n

        self._writer.write_uint8(int(instruction.ins_type.value.byte_code))
        self._writer.write_uint8(int(instruction.ins_type.value.qualifier))

        # Handle instruction-specific arguments
        if instruction.ins_type in {
            NCSInstructionType.DECISP,
            NCSInstructionType.INCISP,
            NCSInstructionType.DECIBP,
            NCSInstructionType.INCIBP,
        }:
            self._writer.write_int32(instruction.args[0], big=True)

        elif instruction.ins_type in {NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP, NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP}:
            self._writer.write_int32(instruction.args[0], big=True)
            self._writer.write_uint16(4, big=True)  # TODO: 12 for float support

        elif instruction.ins_type == NCSInstructionType.CONSTF:
            self._writer.write_single(instruction.args[0], big=True)
        elif instruction.ins_type == NCSInstructionType.CONSTO:
            self._writer.write_uint32(instruction.args[0], big=True)
        elif instruction.ins_type == NCSInstructionType.CONSTI:
            self._writer.write_int32(instruction.args[0], big=True)
        elif instruction.ins_type == NCSInstructionType.CONSTS:
            # CONSTS with string length and string data
            self._writer.write_string(instruction.args[0], big=True, prefix_length=2)

        elif instruction.ins_type == NCSInstructionType.ACTION:
            # ACTION with routine number and argument count
            self._writer.write_uint16(instruction.args[0], big=True)
            self._writer.write_uint8(instruction.args[1], big=True)

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.LOGANDII,
            NCSInstructionType.LOGORII,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.INCORII,
            NCSInstructionType.EXCORII,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.BOOLANDII:  # noqa: SIM114
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.EQUALII,
            NCSInstructionType.EQUALFF,
            NCSInstructionType.EQUALOO,
            NCSInstructionType.EQUALEFFEFF,
            NCSInstructionType.EQUALEVTEVT,
            NCSInstructionType.EQUALLOCLOC,
            NCSInstructionType.EQUALTALTAL,
            NCSInstructionType.EQUALSS,
        }:
            ...

        elif instruction.ins_type in {
            NCSInstructionType.NEQUALII,
            NCSInstructionType.NEQUALFF,
            NCSInstructionType.NEQUALOO,
            NCSInstructionType.NEQUALEFFEFF,
            NCSInstructionType.NEQUALEVTEVT,
            NCSInstructionType.NEQUALLOCLOC,
            NCSInstructionType.NEQUALTALTAL,
            NCSInstructionType.NEQUALSS,
        }:
            ...

        elif instruction.ins_type in {
            NCSInstructionType.EQUALTT,
            NCSInstructionType.NEQUALTT,
        }:
            self._writer.write_uint16(instruction.args[0], big=True)

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.GEQxx,
            NCSInstructionType.GEQII,
            NCSInstructionType.GEQFF,
            # NCSInstructionType.GTxx,
            NCSInstructionType.GTII,
            NCSInstructionType.GTFF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.LTxx,
            NCSInstructionType.LTII,
            NCSInstructionType.LTFF,
            # NCSInstructionType.LExx,
            NCSInstructionType.LEQII,
            NCSInstructionType.LEQFF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.SHLEFTII,
            NCSInstructionType.SHRIGHTII,
            NCSInstructionType.USHRIGHTII,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.ADDII,
            NCSInstructionType.ADDFF,
            NCSInstructionType.ADDFI,
            NCSInstructionType.ADDIF,
            NCSInstructionType.ADDSS,
            NCSInstructionType.ADDVV,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.SUBII,
            NCSInstructionType.SUBFF,
            NCSInstructionType.SUBFI,
            NCSInstructionType.SUBIF,
            NCSInstructionType.SUBVV,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.MULII,
            NCSInstructionType.MULFF,
            NCSInstructionType.MULFI,
            NCSInstructionType.MULIF,
            NCSInstructionType.MULFV,
            NCSInstructionType.MULVF,
        }:
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.DIVII,
            NCSInstructionType.DIVFF,
            NCSInstructionType.DIVFI,
            NCSInstructionType.DIVIF,
            NCSInstructionType.DIVFV,
            NCSInstructionType.DIVVF,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.MODII:  # noqa: SIM114
            ...

        elif instruction.ins_type in {  # noqa: SIM114
            # NCSInstructionType.NEGx,
            NCSInstructionType.NEGI,
            NCSInstructionType.NEGF,
        }:
            ...

        elif instruction.ins_type == NCSInstructionType.COMPI:
            ...

        elif instruction.ins_type == NCSInstructionType.MOVSP:
            # MOVSP to adjust the stack pointer
            self._writer.write_int32(to_signed_32bit(instruction.args[0]), big=True)

        elif (
            instruction.ins_type
            in {
                # NCSInstructionType.STORE_STATEALL,
            }
        ):
            ...

        elif instruction.ins_type in {
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
        }:
            jump = instruction.jump
            assert jump is not None, f"{instruction} has a NoneType jump."
            relative = self._offsets[jump] - self._offsets[instruction]
            self._writer.write_int32(to_signed_32bit(relative), big=True)

        elif instruction.ins_type == NCSInstructionType.RETN:
            ...

        elif instruction.ins_type == NCSInstructionType.DESTRUCT:
            self._writer.write_uint16(instruction.args[0], big=True)
            self._writer.write_int16(to_signed_16bit(instruction.args[1]), big=True)
            self._writer.write_uint16(instruction.args[2], big=True)

        elif instruction.ins_type == NCSInstructionType.NOTI:  # noqa: SIM114
            ...

        elif instruction.ins_type in {NCSInstructionType.SAVEBP, NCSInstructionType.RESTOREBP}:
            ...

        elif instruction.ins_type == NCSInstructionType.STORE_STATE:
            self._writer.write_uint32(instruction.args[0], big=True)
            self._writer.write_uint32(instruction.args[1], big=True)

        elif instruction.ins_type == NCSInstructionType.NOP:  # noqa: SIM114
            ...

        elif instruction.ins_type in {
            NCSInstructionType.RSADDI,
            NCSInstructionType.RSADDF,
            NCSInstructionType.RSADDO,
            NCSInstructionType.RSADDS,
            NCSInstructionType.RSADDEFF,  # ???
            NCSInstructionType.RSADDEVT,  # ???
            NCSInstructionType.RSADDLOC,  # ???
            NCSInstructionType.RSADDTAL,  # ???
        }:
            ...

        else:
            msg = f"Tried to write unsupported instruction ({instruction.ins_type.name}) to NCS"
            raise ValueError(msg)
