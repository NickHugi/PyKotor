from pykotor.resource.formats.ncs.compiler.classes import IntValue, ControlKeyword, IdentifierValue, StringValue, \
    FloatValue
from pykotor.resource.formats.ncs.data import ReturnType

from abc import ABC
from enum import Enum
from typing import Any

from ply.lex import lex


class NssLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.lexer.begin("INITIAL")

    tokens = [
        "STRING_VALUE", "NUMBER_VALUE", "FLOAT_VALUE", "IDENTIFIER_VALUE", "INT_TYPE", "FLOAT_TYPE", "OBJECT_TYPE",
        "VOID_TYPE",  "EVENT_TYPE", "EFFECT_TYPE", "ITEMPROPERTY_TYPE", "LOCATION_TYPE", "STRING_TYPE", "TALENT_TYPE",
        "VECTOR_TYPE", "ACTION_TYPE", "BREAK_CONTROL", "CASE_CONTROL", "DEFAULT_CONTROL", "DO_CONTROL", "ELSE_CONTROL",
        "SWITCH_CONTROL", "WHILE_CONTROL", "FOR_CONTROL", "IF_CONTROL", "TRUE_VALUE", "FALSE_VALUE", "OBJECTSELF_VALUE",
        "OBJECTINVALID_VALUE"
    ]

    # region Value Tokens
    def t_IDENTIFIER_VALUE(self, t):
        r'[a-zA-Z_]+[a-zA-Z0-9_]*'
        t.value = IdentifierValue(t.value)
        return t

    def t_STRING_VALUE(self, t):
        r'\"[^\"]*\"'
        t.value = StringValue(t.value)
        return t

    def t_FLOAT_VALUE(self, t):
        r'[0-9]+\.[0-9]+'
        t.value = FloatValue(float(t.value))
        return t

    def t_INT_VALUE(self, t):
        r'[0-9]+'
        t.value = IntValue(int(t.value))
        return t

    def t_TRUE_VALUE(self, t):
        r'TRUE'
        t.value = IntValue(1)
        return t

    def t_FALSE_VALUE(self, t):
        r'FALSE'
        t.value = IntValue(0)
        return t

    def t_OBJECTSELF_VALUE(self, t):
        r'OBJECT_SELF'
        t.value = IntValue(0)
        return t

    def t_OBJECTINVALID_VALUE(self, t):
        r'OBJECT_INVALID'
        t.value = IntValue(-1)
        return t
    # endregion

    # region Type Tokens
    def t_INT_TYPE(self, t):
        r'int'
        t.value = ReturnType.INT
        return t

    def t_FLOAT_TYPE(self, t):
        r'float'
        t.value = ReturnType.FLOAT
        return t

    def t_OBJECT_TYPE(self, t):
        r'object'
        t.value = ReturnType.OBJECT
        return t

    def t_VOID_TYPE(self, t):
        r'void'
        t.value = ReturnType.VOID
        return t

    def t_EVENT_TYPE(self, t):
        r'event'
        t.value = ReturnType.EVENT
        return t

    def t_EFFECT_TYPE(self, t):
        r'effect'
        t.value = ReturnType.EFFECT
        return t

    def t_ITEMPROPERTY_TYPE(self, t):
        r'itemproperty'
        t.value = ReturnType.ITEMPROPERTY
        return t

    def t_LOCATION_TYPE(self, t):
        r'location'
        t.value = ReturnType.LOCATION
        return t

    def t_STRING_TYPE(self, t):
        r'string'
        t.value = ReturnType.STRING
        return t

    def t_TALENT_TYPE(self, t):
        r'talent'
        t.value = ReturnType.TALENT
        return t

    def t_ACTION_TYPE(self, t):
        r'action'
        t.value = ReturnType.ACTION
        return t

    def t_VECTOR_TYPE(self, t):
        r'vector'
        t.value = ReturnType.VECTOR
        return t
    # endregion

    # region Control Tokens
    def t_BREAK_CONTROL(self, t):
        r'break'
        t.value = ControlKeyword.BREAK
        return t

    def t_CASE_CONTROL(self, t):
        r'case'
        t.value = ControlKeyword.CASE
        return t

    def t_DEFAULT_CONTROL(self, t):
        r'default'
        t.value = ControlKeyword.DEFAULT
        return t

    def t_DO_CONTROL(self, t):
        r'do'
        t.value = ControlKeyword.DO
        return t

    def t_ELSE_CONTROL(self, t):
        r'else'
        t.value = ControlKeyword.ELSE
        return t

    def t_SWITCH_CONTROL(self, t):
        r'switch'
        t.value = ControlKeyword.SWITCH
        return t

    def t_WHILE_CONTROL(self, t):
        r'while'
        t.value = ControlKeyword.WHILE
        return t

    def t_FOR_CONTROL(self, t):
        r'for'
        t.value = ControlKeyword.FOR
        return t

    def t_IF_CONTROL(self, t):
        r'if'
        t.value = ControlKeyword.IF
        return t
    # endregion

