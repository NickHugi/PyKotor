from __future__ import annotations

import struct
from io import BufferedIOBase


class Decoder:
    DECOCT_CPDOWNSP = 1
    DECOCT_RSADD = 2
    DECOCT_CPTOPSP = 3
    DECOCT_CONST = 4
    DECOCT_ACTION = 5
    DECOCT_LOGANDII = 6
    DECOCT_LOGORII = 7
    DECOCT_INCORII = 8
    DECOCT_EXCORII = 9
    DECOCT_BOOLANDII = 10
    DECOCT_EQUAL = 11
    DECOCT_NEQUAL = 12
    DECOCT_GEQ = 13
    DECOCT_GT = 14
    DECOCT_LT = 15
    DECOCT_LEQ = 16
    DECOCT_SHLEFTII = 17
    DECOCT_SHRIGHTII = 18
    DECOCT_USHRIGHTII = 19
    DECOCT_ADD = 20
    DECOCT_SUB = 21
    DECOCT_MUL = 22
    DECOCT_DIV = 23
    DECOCT_MOD = 24
    DECOCT_NEG = 25
    DECOCT_COMP = 26
    DECOCT_MOVSP = 27
    DECOCT_STATEALL = 28
    DECOCT_JMP = 29
    DECOCT_JSR = 30
    DECOCT_JZ = 31
    DECOCT_RETN = 32
    DECOCT_DESTRUCT = 33
    DECOCT_NOT = 34
    DECOCT_DECISP = 35
    DECOCT_INCISP = 36
    DECOCT_JNZ = 37
    DECOCT_CPDOWNBP = 38
    DECOCT_CPTOPBP = 39
    DECOCT_DECIBP = 40
    DECOCT_INCIBP = 41
    DECOCT_SAVEBP = 42
    DECOCT_RESTOREBP = 43
    DECOCT_STORE_STATE = 44
    DECOCT_NOP = 45
    DECOCT_T = 66

    def __init__(self, in_stream: BufferedIOBase, actions):
        self.in_stream = in_stream
        self.actions = actions
        self.pos = 0

    def decode(self) -> str:
        self.read_header()
        commands = self.read_commands()
        return commands

    def read_commands(self) -> str:
        strbuffer: list[str] = []
        while self.read_command(strbuffer) != -1:
            pass
        return "".join(strbuffer)

    def read_command(self, strbuffer: list[str]) -> int:
        buffer = bytearray(1)
        commandpos: int = self.pos
        status: int = self.in_stream.readinto(buffer)
        self.pos += 1
        if status == -1:
            return status
        strbuffer.append(self.get_command(buffer[0]))
        strbuffer.append(" " + str(commandpos))
        try:
            if buffer[0] in [1, 3, 38, 39]:
                strbuffer.append(" " + self.read_byte_as_string())
                strbuffer.append(" " + self.read_signed_int())
                strbuffer.append(" " + self.read_unsigned_short())
            elif buffer[0] in [2, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 32, 34, 42, 43, 45]:
                strbuffer.append(" " + self.read_byte_as_string())
            elif buffer[0] == 4:
                b: int = self.read_byte()
                strbuffer.append(" " + str(b))
                if b == 3:
                    strbuffer.append(" " + self.read_unsigned_int())
                elif b == 6:
                    strbuffer.append(" " + self.read_signed_int())
                elif b == 4:
                    strbuffer.append(" " + self.read_float())
                elif b == 5:
                    strbuffer.append(" " + self.read_string())
                else:
                    raise RuntimeError("Unknown or unexpected constant type: " + str(b))
            elif buffer[0] == 5:
                strbuffer.append(" " + self.read_byte_as_string())
                strbuffer.append(" " + self.read_unsigned_short())
                strbuffer.append(" " + self.read_byte_as_string())
            elif buffer[0] in [11, 12]:
                b = self.read_byte()
                strbuffer.append(" " + str(b))
                if b == 36:
                    strbuffer.append(" " + self.read_unsigned_short())
            elif buffer[0] in [27, 29, 30, 31, 35, 36, 37, 40, 41]:
                strbuffer.append(" " + self.read_byte_as_string())
                strbuffer.append(" " + self.read_signed_int())
            elif buffer[0] == 28:
                strbuffer.append(" " + self.read_byte_as_string())
            elif buffer[0] == 33:
                strbuffer.append(" " + self.read_byte_as_string())
                strbuffer.append(" " + self.read_unsigned_short())
                strbuffer.append(" " + self.read_unsigned_short())
                strbuffer.append(" " + self.read_unsigned_short())
            elif buffer[0] == 44:
                strbuffer.append(" " + self.read_byte_as_string())
                strbuffer.append(" " + self.read_signed_int())
                strbuffer.append(" " + self.read_signed_int())
            elif buffer[0] == 66:
                strbuffer.append(" " + self.read_signed_int())
            else:
                raise RuntimeError("Unknown command type: " + str(buffer[0]))
        except Exception:
            print("error in .ncs file at pos " + str(self.pos))
            raise
        strbuffer.append("; ")
        return 1

    def read_byte(self) -> int:
        buffer = bytearray(1)
        status = self.in_stream.readinto(buffer)
        self.pos += 1
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        return buffer[0]

    def read_byte_as_string(self) -> str:
        return str(self.read_byte())

    def read_unsigned_int(self) -> str:
        buffer = bytearray(4)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += 4
        num = 0
        for i in range(4):
            num |= buffer[i] & 0xFF
            if i < 3:
                num <<= 8
        return str(num)

    def read_signed_int(self) -> str:
        buffer = bytearray(4)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += 4
        i = int.from_bytes(buffer, byteorder="big", signed=True)
        return str(i)

    def read_unsigned_short(self) -> str:
        buffer = bytearray(2)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += 2
        i = int.from_bytes(buffer, byteorder="big", signed=False)
        return str(i)

    def read_float(self) -> str:
        buffer = bytearray(4)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += 4
        i = int.from_bytes(buffer, byteorder="big", signed=False)
        f: float = struct.unpack(">f", struct.pack(">I", i))[0]
        return str(f)

    def read_string(self) -> str:
        buffer = bytearray(2)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += 2
        size: int = int.from_bytes(buffer, byteorder="big", signed=False)
        buffer = bytearray(size)
        status = self.in_stream.readinto(buffer)
        if status == -1:
            raise RuntimeError("Unexpected EOF")
        self.pos += size
        return '"' + buffer.decode("ascii") + '"'

    def read_header(self):
        buffer = bytearray(8)
        header = bytearray([78, 67, 83, 32, 86, 49, 46, 48])
        self.in_stream.readinto(buffer)
        self.pos += 8
        if buffer != header:
            raise RuntimeError("The data file is not an NCS V1.0 file.")

    def get_command(self, command: int) -> str:
        if command == 1:
            return "CPDOWNSP"
        elif command == 2:
            return "RSADD"
        elif command == 3:
            return "CPTOPSP"
        elif command == 4:
            return "CONST"
        elif command == 5:
            return "ACTION"
        elif command == 6:
            return "LOGANDII"
        elif command == 7:
            return "LOGORII"
        elif command == 8:
            return "INCORII"
        elif command == 9:
            return "EXCORII"
        elif command == 10:
            return "BOOLANDII"
        elif command == 11:
            return "EQUAL"
        elif command == 12:
            return "NEQUAL"
        elif command == 13:
            return "GEQ"
        elif command == 14:
            return "GT"
        elif command == 15:
            return "LT"
        elif command == 16:
            return "LEQ"
        elif command == 17:
            return "SHLEFTII"
        elif command == 18:
            return "SHRIGHTII"
        elif command == 19:
            return "USHRIGHTII"
        elif command == 20:
            return "ADD"
        elif command == 21:
            return "SUB"
        elif command == 22:
            return "MUL"
        elif command == 23:
            return "DIV"
        elif command == 24:
            return "MOD"
        elif command == 25:
            return "NEG"
        elif command == 26:
            return "COMP"
        elif command == 27:
            return "MOVSP"
        elif command == 28:
            return "STATEALL"
        elif command == 29:
            return "JMP"
        elif command == 30:
            return "JSR"
        elif command == 31:
            return "JZ"
        elif command == 32:
            return "RETN"
        elif command == 33:
            return "DESTRUCT"
        elif command == 34:
            return "NOT"
        elif command == 35:
            return "DECISP"
        elif command == 36:
            return "INCISP"
        elif command == 37:
            return "JNZ"
        elif command == 38:
            return "CPDOWNBP"
        elif command == 39:
            return "CPTOPBP"
        elif command == 40:
            return "DECIBP"
        elif command == 41:
            return "INCIBP"
        elif command == 42:
            return "SAVEBP"
        elif command == 43:
            return "RESTOREBP"
        elif command == 44:
            return "STORE_STATE"
        elif command == 45:
            return "NOP"
        elif command == 66:
            return "T"
        else:
            raise RuntimeError("Unknown command code: " + str(command))
