from __future__ import annotations

from pykotor.resource.formats.ncs.ncs_types import NCSType, NCSTypeCode


class Type:
    """Wrapper around NCSType to match DeNCS Type.java interface.
    
    This allows us to reuse the existing NCSType implementation
    while maintaining compatibility with DeNCS code.
    """
    VT_NONE = 0
    VT_STACK = 1
    VT_INTEGER = 3
    VT_FLOAT = 4
    VT_STRING = 5
    VT_OBJECT = 6
    VT_EFFECT = 16
    VT_EVENT = 17
    VT_LOCATION = 18
    VT_TALENT = 19
    VT_INTINT = 32
    VT_FLOATFLOAT = 33
    VT_OBJECTOBJECT = 34
    VT_STRINGSTRING = 35
    VT_STRUCTSTRUCT = 36
    VT_INTFLOAT = 37
    VT_FLOATINT = 38
    VT_EFFECTEFFECT = 48
    VT_EVENTEVENT = 49
    VT_LOCLOC = 50
    VT_TALTAL = 51
    VT_VECTORVECTOR = 58
    VT_VECTORFLOAT = 59
    VT_FLOATVECTOR = 60
    VT_VECTOR = -16
    VT_STRUCT = -15
    VT_INVALID = -1

    def __init__(self, type_val: int | str):
        if isinstance(type_val, str):
            self.type = self.decode(type_val)
            self.size = self.type_size(self.type) // 4
        else:
            self.type = type_val
            self.size = 1

    @staticmethod
    def parse_type(type_str: str):
        return Type(type_str)

    def close(self):
        pass

    def byte_value(self) -> int:
        return self.type

    def __str__(self) -> str:
        return self.to_string(self.type)

    @staticmethod
    def to_string(atype):
        return Type.to_string(atype.type)

    @staticmethod
    def to_string_static(type_val: int) -> str:
        if type_val == 3:
            return "int"
        elif type_val == 4:
            return "float"
        elif type_val == 5:
            return "string"
        elif type_val == 6:
            return "object"
        elif type_val == 16:
            return "effect"
        elif type_val == 18:
            return "location"
        elif type_val == 19:
            return "talent"
        elif type_val == 32:
            return "intint"
        elif type_val == 33:
            return "floatfloat"
        elif type_val == 34:
            return "objectobject"
        elif type_val == 35:
            return "stringstring"
        elif type_val == 36:
            return "structstruct"
        elif type_val == 37:
            return "intfloat"
        elif type_val == 38:
            return "floatint"
        elif type_val == 48:
            return "effecteffect"
        elif type_val == 49:
            return "eventevent"
        elif type_val == 50:
            return "locloc"
        elif type_val == 51:
            return "taltal"
        elif type_val == 58:
            return "vectorvector"
        elif type_val == 59:
            return "vectorfloat"
        elif type_val == 60:
            return "floatvector"
        elif type_val == 0:
            return "void"
        elif type_val == 1:
            return "stack"
        elif type_val == -16:
            return "vector"
        elif type_val == -1:
            return "invalid"
        elif type_val == -15:
            return "struct"
        else:
            return "unknown"

    def to_decl_string(self) -> str:
        return self.__str__()

    def size(self) -> int:
        return self.size

    def is_typed(self) -> bool:
        return self.type != -1

    def to_value_string(self) -> str:
        return str(self.type)

    @staticmethod
    def decode(type_str: str) -> int:
        if type_str == "void":
            return 0
        elif type_str == "int":
            return 3
        elif type_str == "float":
            return 4
        elif type_str == "string":
            return 5
        elif type_str == "object":
            return 6
        elif type_str == "effect":
            return 16
        elif type_str == "event":
            return 17
        elif type_str == "location":
            return 18
        elif type_str == "talent":
            return 19
        elif type_str == "vector":
            return -16
        elif type_str == "action":
            return 0
        elif type_str == "INT":
            return 3
        elif type_str == "OBJECT_ID":
            return 6
        else:
            raise RuntimeError("Attempted to get unknown type " + type_str)

    def type_size(self) -> int:
        return self.type_size(self.type)

    @staticmethod
    def type_size(type_val: int | str) -> int:
        if isinstance(type_val, str):
            return Type.type_size(Type.decode(type_val))
        if type_val == 3:
            return 4
        elif type_val == 4:
            return 4
        elif type_val == 5:
            return 4
        elif type_val == 6:
            return 4
        elif type_val == 16:
            return 4
        elif type_val == 18:
            return 4
        elif type_val == 19:
            return 4
        elif type_val == 17:
            return 4
        elif type_val == 0:
            return 0
        elif type_val == -16:
            return 12
        else:
            raise RuntimeError("Unknown type code: " + str(type_val))

    def get_element(self, pos: int):
        if pos != 1:
            raise RuntimeError("Position > 1 for type, not struct")
        return self

    def __eq__(self, obj):
        return isinstance(obj, Type) and self.type == obj.type

    def equals(self, type_val: int) -> bool:
        return self.type == type_val

    def __hash__(self):
        return self.type

