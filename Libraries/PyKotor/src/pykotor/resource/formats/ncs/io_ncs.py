from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.ncs.ncs_data import NCS, NCSByteCode, NCSInstruction, NCSInstructionType, NCSInstructionTypeValue
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

# NCS file format constants
NCS_HEADER_MAGIC_BYTE = 0x42
NCS_HEADER_SIZE = 13  # "NCS " (4) + "V1.0" (4) + magic_byte (1) + size (4)


class NCSBinaryReader(ResourceReader):
    """Reads NCS (NWScript Compiled Script) files.
    
    NCS files contain compiled bytecode for NWScript, the scripting language used in KotOR.
    Instructions include operations, constants, function calls, jumps, and control flow.
    
    References:
    ----------
        vendor/reone/src/libs/script/format/ncsreader.cpp:28-40 (NCS header reading)
        vendor/reone/src/libs/script/format/ncsreader.cpp:42-195 (instruction reading)
        vendor/xoreos-tools/src/nwscript/decompiler.cpp (NCS decompilation)
        vendor/xoreos-docs/specs/torlack/ncs.html (NCS format specification)
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._ncs: NCS | None = None
        self._instructions: dict[int, NCSInstruction] = {}
        self._jumps: list[tuple[NCSInstruction, int]] = []

    @autoclose
    def load(self, *, auto_close: bool = True) -> NCS:
        """Loads an NCS file from the reader.

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
        self._jumps = []

        # Read the header fields
        # vendor/reone/src/libs/script/format/ncsreader.cpp:31-32
        magic_byte = self._reader.read_uint8()  # Position 8
        total_size = self._reader.read_uint32(big=True)  # Positions 9-12: Total file size

        # Validate header
        if magic_byte != NCS_HEADER_MAGIC_BYTE:
            msg = f"Invalid NCS header magic byte: expected 0x{NCS_HEADER_MAGIC_BYTE:02X}, got 0x{magic_byte:02X}"
            raise ValueError(msg)

        # Validate size field
        actual_file_size = self._reader.size()
        if total_size > actual_file_size:
            msg = (
                f"NCS size field ({total_size}) is larger than actual file size ({actual_file_size}). "
                f"File may be corrupted or truncated."
            )
            raise ValueError(msg)

        # Check for empty or minimal NCS files
        if total_size <= NCS_HEADER_SIZE:
            # File has only a header, no instructions
            # This is technically valid but unusual
            self._ncs.instructions = []
            return self._ncs

        # Now at position 13, read instructions until we reach total_size
        # total_size is the end position (includes the header)
        code_end_position = total_size

        # Safety: don't read beyond actual file size
        safe_end_position = min(code_end_position, actual_file_size)

        while self._reader.position() < safe_end_position and self._reader.remaining() > 0:
            offset = self._reader.position()

            try:
                self._instructions[offset] = self._read_instruction()
            except ValueError as e:
                error_msg = str(e)

                # Check if this is zero-padding that slipped through due to incorrect size field
                if "Unknown NCS bytecode 0x00" in error_msg:
                    # Peek ahead to confirm this is just padding
                    self._reader.seek(offset)

                    # Read remaining bytes up to the safe end position
                    bytes_to_check = min(self._reader.remaining(), safe_end_position - offset)
                    remaining_data = self._reader.read_bytes(bytes_to_check)

                    if all(b == 0 for b in remaining_data):
                        # This is zero-padding - the size field incorrectly includes padding
                        import sys  # noqa: PLC0415
                        print(
                            f"Warning: NCS file has incorrect size field (includes zero-padding). "
                            f"Size field: {total_size}, actual code ends at: {offset}, "
                            f"found {len(remaining_data)} bytes of padding",
                            file=sys.stderr
                        )
                        break

                    # Not all zeros - this is genuinely corrupted data
                    # Show diagnostic information
                    self._reader.seek(offset)
                    diagnostic_bytes = self._reader.read_bytes(min(32, self._reader.remaining()))
                    diagnostic_hex = " ".join(f"{b:02X}" for b in diagnostic_bytes)

                    enhanced_msg = (
                        f"{error_msg}\n"
                        f"  File size field: {total_size}, current offset: {offset}\n"
                        f"  Next 32 bytes (hex): {diagnostic_hex}\n"
                        f"  This indicates the NCS file is genuinely corrupted or uses an unknown format variant."
                    )
                    raise ValueError(enhanced_msg) from e

                # Re-raise other errors with additional context
                enhanced_msg = f"Failed to parse NCS instruction at offset {offset}: {error_msg}"
                raise ValueError(enhanced_msg) from e

        for instruction, jumpToOffset in self._jumps:
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
        instruction_offset = self._reader.position()
        byte_code_value = self._reader.read_uint8()
        qualifier = self._reader.read_uint8()

        # Try to convert to NCSByteCode enum
        try:
            byte_code = NCSByteCode(byte_code_value)
        except ValueError as e:
            # Provide detailed diagnostic information for unknown bytecodes
            # Read some context bytes around the error position
            context_size = 16
            context_start = max(0, instruction_offset - context_size)
            current_pos = self._reader.position()

            self._reader.seek(context_start)
            context_bytes = self._reader.read_bytes(min(context_size * 2, self._reader.size() - context_start))
            context_hex = " ".join(f"{b:02X}" for b in context_bytes)

            self._reader.seek(current_pos)  # Restore position

            msg = (
                f"Unknown NCS bytecode 0x{byte_code_value:02X} with qualifier 0x{qualifier:02X} at offset {instruction_offset}.\n"
                f"  Context (hex): {context_hex}\n"
                f"  This NCS file may be corrupted, from an unsupported NCS variant, or have an incorrect size field."
            )
            raise ValueError(msg) from e

        type_value = NCSInstructionTypeValue(byte_code, qualifier)

        instruction = NCSInstruction()
        instruction.offset = instruction_offset

        # Special handling for RESERVED opcode - it appears with various qualifiers
        # Treat all RESERVED variants as simple 2-byte no-ops
        if byte_code == NCSByteCode.RESERVED:
            # Use RESERVED (0x00, 0x00) as the canonical type regardless of actual qualifier
            instruction.ins_type = NCSInstructionType.RESERVED
        else:
            try:
                instruction.ins_type = NCSInstructionType(type_value)
            except ValueError as e:
                # Unknown bytecode/qualifier combination - the bytecode exists but this specific
                # combination with the qualifier is not recognized
                msg = (
                    f"Unknown NCS instruction type combination: "
                    f"bytecode=0x{byte_code_value:02X} ({byte_code.name}), "
                    f"qualifier=0x{qualifier:02X} at offset {instruction_offset}.\n"
                    f"  The bytecode is recognized but this qualifier combination is not supported."
                )
                raise ValueError(msg) from e

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
            # Object constants are stored as signed 32-bit integers, not 16-bit
            # See DeNCS Decoder.java case 4, subcase 6 (OBJECT type uses readSignedInt)
            instruction.args.extend([self._reader.read_int32(big=True)])

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
            self._jumps.append((instruction, jumpOffset))

        elif instruction.ins_type == NCSInstructionType.DESTRUCT:
            instruction.args.extend(
                [
                    self._reader.read_uint16(big=True),
                    self._reader.read_int16(big=True),
                    self._reader.read_uint16(big=True),
                ],
            )

        elif instruction.ins_type in {
            NCSInstructionType.DECxSP,
            NCSInstructionType.INCxSP,
            NCSInstructionType.DECxBP,
            NCSInstructionType.INCxBP,
        }:
            instruction.args.extend([self._reader.read_uint32(big=True)])

        elif instruction.ins_type == NCSInstructionType.STORE_STATE:
            instruction.args.extend([self._reader.read_uint32(big=True), self._reader.read_uint32(big=True)])

        elif instruction.ins_type in {
            NCSInstructionType.EQUALTT,
            NCSInstructionType.NEQUALTT,
        }:
            # Struct equality comparisons include a size field
            # See DeNCS Decoder.java case 11/12 with qualifier 0x24 (36 = StructStruct)
            instruction.args.extend([self._reader.read_uint16(big=True)])

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

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.RESERVED,
            NCSInstructionType.RESERVED_01,
        }:
            # Reserved/unknown opcodes - treat as 2-byte no-ops with no arguments
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
        self._offsets: dict[int, int] = {}
        self._sizes: dict[int, int] = {}

    @autoclose
    def write(self, *, auto_close: bool = True):
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
        offset = NCS_HEADER_SIZE
        for instruction in self._ncs.instructions:
            inst_id = id(instruction)
            instruction_size = self.determine_size(instruction)
            self._sizes[inst_id] = instruction_size
            self._offsets[inst_id] = offset
            offset += instruction_size

        self._writer.write_string("NCS ")
        self._writer.write_string("V1.0")
        self._writer.write_uint8(NCS_HEADER_MAGIC_BYTE)
        self._writer.write_uint32(offset, big=True)

        for instruction in self._ncs.instructions:
            self._write_instruction(instruction)

    def determine_size(self, instruction: NCSInstruction) -> int:  # TODO(th3w1zard1): This function is unfinished and is missing defs.
        """Determines the size of an NCS instruction in bytes.

        Based on DeNCS Decoder.java readCommand method which shows complete instruction formats.

        Args:
        ----
            instruction: NCSInstruction - The instruction to determine size for

        Returns:
        -------
            int - The size of the instruction in bytes
        """
        size = 2  # Base size for opcode and qualifier bytes

        # Copy operations: 1 byte qualifier + 4 bytes offset + 2 bytes size = 7 bytes additional
        # DeNCS case 1, 3, 38, 39
        if instruction.ins_type in {
            NCSInstructionType.CPDOWNSP,
            NCSInstructionType.CPTOPSP,
            NCSInstructionType.CPDOWNBP,
            NCSInstructionType.CPTOPBP,
        }:
            size += 6  # 1 + 4 + 2 - 1 (qualifier already in base) = 6

        # STORE_STATE: 1 byte qualifier + 4 bytes + 4 bytes = 9 bytes additional
        # DeNCS case 44
        elif instruction.ins_type == NCSInstructionType.STORE_STATE:
            size += 8  # 1 + 4 + 4 - 1 = 8

        # Struct equality: 1 byte qualifier + 2 bytes size = 3 bytes additional
        # DeNCS case 11, 12 with qualifier 0x24
        elif instruction.ins_type in {
            NCSInstructionType.NEQUALTT,
            NCSInstructionType.EQUALTT,
        }:
            size += 2  # 1 + 2 - 1 = 2

        # Jump/Move operations: 1 byte qualifier + 4 bytes offset = 5 bytes additional
        # DeNCS case 27, 29, 30, 31, 35, 36, 37, 40, 41
        elif instruction.ins_type in {
            NCSInstructionType.MOVSP,
            NCSInstructionType.JMP,
            NCSInstructionType.JSR,
            NCSInstructionType.JZ,
            NCSInstructionType.JNZ,
            NCSInstructionType.DECxSP,
            NCSInstructionType.INCxSP,
            NCSInstructionType.DECxBP,
            NCSInstructionType.INCxBP,
        }:
            size += 4  # 1 + 4 - 1 = 4

        # Constants with 4-byte values
        # DeNCS case 4 with subcases for int/float/object
        elif instruction.ins_type in {
            NCSInstructionType.CONSTI,
            NCSInstructionType.CONSTF,
            NCSInstructionType.CONSTO,
        }:
            size += 4  # 4 bytes for the constant value

        # String constant: 2 bytes length + string data
        # DeNCS case 4 subcase 5 (string)
        elif instruction.ins_type == NCSInstructionType.CONSTS:
            size += 2 + len(instruction.args[0])  # 2 bytes length prefix + string

        # ACTION: 2 bytes routine number + 1 byte argument count
        # DeNCS case 5
        elif instruction.ins_type == NCSInstructionType.ACTION:
            size += 3  # 2 + 1 = 3

        # DESTRUCT: 1 byte qualifier + 2 bytes + 2 bytes + 2 bytes = 7 bytes additional
        # DeNCS case 33
        elif instruction.ins_type == NCSInstructionType.DESTRUCT:
            size += 6  # 1 + 2 + 2 + 2 - 1 = 6

        # All other instructions have just opcode + qualifier (2 bytes total)
        # This includes: RSADD variants, logical/arithmetic ops, RETN, SAVEBP, RESTOREBP, etc.
        # DeNCS case 2, 6-10, 13-26, 32, 34, 42, 43, 45

        return size

    def _write_instruction(self, instruction: NCSInstruction):  # TODO(th3w1zard1): This function is unfinished and is missing defs.
        """Writes an instruction to the NCS binary stream.

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

        def to_signed_32bit(n: int) -> int:  # FIXME(th3w1zard1): Presumably this issue happens further up the call stack, fix later.
            """Convert unsigned 32-bit integer representation to signed.

            Handles edge cases where values may be stored as unsigned but need
            to be interpreted/written as signed two's complement integers.
            Python's int type can represent any value, but when reading from
            binary data or external sources, values may need conversion.

            Args:
            ----
                n: Integer value, possibly in unsigned representation

            Returns:
            -------
                Signed 32-bit integer value
            """
            # Convert to signed if value is in upper half of unsigned 32-bit range
            if n >= 2**31:
                n -= 2**32
            return n

        def to_signed_16bit(n: int) -> int:  # FIXME(th3w1zard1): Only seen this issue happen with 32bit but better safe than sorry, remove this once above issue is fixed.
            """Convert unsigned 16-bit integer representation to signed.

            Similar to to_signed_32bit but for 16-bit values.

            Args:
            ----
                n: Integer value, possibly in unsigned representation

            Returns:
            -------
                Signed 16-bit integer value
            """
            if n >= 2**15:
                n -= 2**16
            return n

        self._writer.write_uint8(int(instruction.ins_type.value.byte_code))
        self._writer.write_uint8(int(instruction.ins_type.value.qualifier))

        # Handle instruction-specific arguments
        if instruction.ins_type in {
            NCSInstructionType.DECxSP,
            NCSInstructionType.INCxSP,
            NCSInstructionType.DECxBP,
            NCSInstructionType.INCxBP,
        }:
            self._writer.write_int32(to_signed_32bit(instruction.args[0]), big=True)

        elif instruction.ins_type in {NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP, NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP}:
            self._writer.write_int32(instruction.args[0], big=True)
            # Size argument: typically 4 for most types, 12 for vectors (3 floats)
            # The args[1] should contain the actual size value from compilation
            size_value = instruction.args[1] if len(instruction.args) > 1 else 4
            self._writer.write_uint16(size_value, big=True)

        elif instruction.ins_type == NCSInstructionType.CONSTF:
            self._writer.write_single(instruction.args[0], big=True)
        elif instruction.ins_type == NCSInstructionType.CONSTO:
            # Object constants are stored as signed 32-bit integers
            # See DeNCS Decoder.java case 4, subcase 6
            self._writer.write_int32(instruction.args[0], big=True)
        elif instruction.ins_type == NCSInstructionType.CONSTI:
            # Integer constants stored as unsigned 32-bit per DeNCS Decoder.java line 137
            # Convert to signed representation for struct packing
            self._writer.write_int32(to_signed_32bit(instruction.args[0]), big=True)
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
            instruction_id = id(instruction)
            jump_id = id(jump)
            relative = self._offsets[jump_id] - self._offsets[instruction_id]
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

        elif instruction.ins_type in {  # noqa: SIM114
            NCSInstructionType.RESERVED,
            NCSInstructionType.RESERVED_01,
        }:
            # Reserved/unknown opcodes - no arguments to write
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
