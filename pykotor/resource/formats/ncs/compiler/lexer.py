import operator

from pykotor.common.script import DataType
from pykotor.resource.formats.ncs import NCSInstructionType
from pykotor.resource.formats.ncs.compiler.classes import IntExpression, ControlKeyword, StringExpression, \
    FloatExpression, Identifier, Operator, BinaryOperatorMapping, UnaryOperatorMapping, OperatorMapping

from abc import ABC
from enum import Enum
from typing import Any

import ply.lex as lex


class NssLexer:
    def __init__(self, errorlog=lex.NullLogger()):
        self.lexer = lex.lex(module=self, errorlog=errorlog)
        self.lexer.begin("INITIAL")

    tokens = [
        "STRING_VALUE", "INT_VALUE", "FLOAT_VALUE", "IDENTIFIER", "INT_TYPE", "FLOAT_TYPE", "OBJECT_TYPE",
        "VOID_TYPE",  "EVENT_TYPE", "EFFECT_TYPE", "ITEMPROPERTY_TYPE", "LOCATION_TYPE", "STRING_TYPE", "TALENT_TYPE",
        "VECTOR_TYPE", "ACTION_TYPE", "BREAK_CONTROL", "CASE_CONTROL", "DEFAULT_CONTROL", "DO_CONTROL", "ELSE_CONTROL",
        "SWITCH_CONTROL", "WHILE_CONTROL", "FOR_CONTROL", "IF_CONTROL", "TRUE_VALUE", "FALSE_VALUE", "OBJECTSELF_VALUE",
        "OBJECTINVALID_VALUE", "ADD", "MINUS", "MULTIPLY", "DIVIDE",
        "MOD", "EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN",
        "LESS_THAN_OR_EQUALS", "GREATER_THAN_OR_EQUALS", "AND", "OR",
        "NOT", "BITWISE_AND", "BITWISE_OR", "BITWISE_LEFT",
        "BITWISE_RIGHT", "BITWISE_XOR", "BITWISE_NOT", "COMMENT", "MULTILINE_COMMENT",
        "INCLUDE", "RETURN", "ADDITION_ASSIGNMENT_OPERATOR", "SUBTRACTION_ASSIGNMENT_OPERATOR",
        "MULTIPLICATION_ASSIGNMENT_OPERATOR", "DIVISION_ASSIGNMENT_OPERATOR", "CONTINUE_CONTROL",
        "STRUCT"
    ]

    literals = [
        '{', '}', '(', ')', ';', '=', ',', ':', '.'
    ]

    t_ignore = " \t\n\r"

    def t_COMMENT(self, t):
        r'//[^\n]*\n'
        pass

    def t_MULTILINE_COMMENT(self, t):
        r'/\*[^\*/]*\*/'
        pass

    def t_INCLUDE(self, t):
        '\#include'
        return t

    # region Control Tokens
    def t_BREAK_CONTROL(self, t):
        r'break'
        t.value = ControlKeyword.BREAK
        return t

    def t_CONTINUE_CONTROL(self, t):
        r'continue'
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

    def t_RETURN(self, t):
        r'return'
        t.value = ControlKeyword.RETURN
        return t
    # endregion

    # region Type Tokens
    def t_STRUCT(self, t):
        r'struct'
        t.value = DataType.STRUCT
        return t

    def t_INT_TYPE(self, t):
        r'int'
        t.value = DataType.INT
        return t

    def t_FLOAT_TYPE(self, t):
        r'float'
        t.value = DataType.FLOAT
        return t

    def t_OBJECT_TYPE(self, t):
        r'object'
        t.value = DataType.OBJECT
        return t

    def t_VOID_TYPE(self, t):
        r'void'
        t.value = DataType.VOID
        return t

    def t_EVENT_TYPE(self, t):
        r'event'
        t.value = DataType.EVENT
        return t

    def t_EFFECT_TYPE(self, t):
        r'effect'
        t.value = DataType.EFFECT
        return t

    def t_ITEMPROPERTY_TYPE(self, t):
        r'itemproperty'
        t.value = DataType.ITEMPROPERTY
        return t

    def t_LOCATION_TYPE(self, t):
        r'location'
        t.value = DataType.LOCATION
        return t

    def t_STRING_TYPE(self, t):
        r'string'
        t.value = DataType.STRING
        return t

    def t_TALENT_TYPE(self, t):
        r'talent'
        t.value = DataType.TALENT
        return t

    def t_ACTION_TYPE(self, t):
        r'action'
        t.value = DataType.ACTION
        return t

    def t_VECTOR_TYPE(self, t):
        r'vector'
        t.value = DataType.VECTOR
        return t
    # endregion

    # region Value Tokens
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_]+[a-zA-Z0-9_]*'
        t.value = Identifier(t.value)
        return t

    def t_STRING_VALUE(self, t):
        r'\"[^\"]*\"'
        t.value = StringExpression(t.value[1:-1])
        return t

    def t_FLOAT_VALUE(self, t):
        r'[0-9]+\.[0-9]+'
        t.value = FloatExpression(float(t.value))
        return t

    def t_INT_VALUE(self, t):
        r'[0-9]+'
        t.value = IntExpression(int(t.value))
        return t

    def t_TRUE_VALUE(self, t):
        r'TRUE'
        t.value = IntExpression(1)
        return t

    def t_FALSE_VALUE(self, t):
        r'FALSE'
        t.value = IntExpression(0)
        return t

    def t_OBJECTSELF_VALUE(self, t):
        r'OBJECT_SELF'
        t.value = IntExpression(0)
        return t

    def t_OBJECTINVALID_VALUE(self, t):
        r'OBJECT_INVALID'
        t.value = IntExpression(-1)
        return t
    # endregion

    def t_INCREMENT(self, t):
        '\+\+'
        t.value = OperatorMapping([
            UnaryOperatorMapping(NCSInstructionType.INCISP, DataType.INT),
        ], [])
        return t

    def t_DECREMENT(self, t):
        '\-\-'
        t.value = OperatorMapping([
            UnaryOperatorMapping(NCSInstructionType.DECISP, DataType.INT),
        ], [])
        return t

    def t_ADDITION_ASSIGNMENT_OPERATOR(self, t):
        '\+\='
        return t

    def t_SUBTRACTION_ASSIGNMENT_OPERATOR(self, t):
        '\-\='
        return t

    def t_MULTIPLICATION_ASSIGNMENT_OPERATOR(self, t):
        '\*\='
        return t

    def t_DIVISION_ASSIGNMENT_OPERATOR(self, t):
        '/\='
        return t

    # region Operators
    def t_BITWISE_LEFT(self, t):
        '<<'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.SHLEFTII, DataType.INT, DataType.INT),
        ])
        return t

    def t_BITWISE_RIGHT(self, t):
        '>>'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.SHRIGHTII, DataType.INT, DataType.INT),
        ])
        return t

    def t_ADD(self, t):
        '\+'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.ADDII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.ADDIF, DataType.INT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.ADDFI, DataType.FLOAT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.ADDFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.ADDVV, DataType.VECTOR, DataType.VECTOR),
            BinaryOperatorMapping(NCSInstructionType.ADDSS, DataType.STRING, DataType.STRING),
        ])
        return t

    def t_MINUS(self, t):
        '-'
        t.value = OperatorMapping([
            UnaryOperatorMapping(NCSInstructionType.NEGI, DataType.INT),
            UnaryOperatorMapping(NCSInstructionType.NEGF, DataType.FLOAT),
        ], [
            BinaryOperatorMapping(NCSInstructionType.SUBII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.SUBIF, DataType.INT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.SUBFI, DataType.FLOAT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.SUBFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.SUBVV, DataType.VECTOR, DataType.VECTOR),
        ])
        return t

    def t_MULTIPLY(self, t):
        '\*'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.MULII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.MULIF, DataType.INT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.MULFI, DataType.FLOAT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.MULFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.MULVF, DataType.VECTOR, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.MULFV, DataType.FLOAT, DataType.VECTOR),
        ])
        return t

    def t_DIVIDE(self, t):
        '/'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.DIVII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.DIVIF, DataType.INT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.DIVFI, DataType.FLOAT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.DIVFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.DIVVF, DataType.VECTOR, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.DIVFV, DataType.FLOAT, DataType.VECTOR),
        ])
        return t

    def t_MOD(self, t):
        '\%'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.MODII, DataType.INT, DataType.INT),
        ])
        return t

    def t_EQUALS(self, t):
        '\=\='
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.EQUALII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.EQUALFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.EQUALOO, DataType.OBJECT, DataType.OBJECT),
            BinaryOperatorMapping(NCSInstructionType.EQUALSS, DataType.STRING, DataType.STRING),
        ])
        return t

    def t_NOT_EQUALS(self, t):
        '\!='
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.NEQUALII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.NEQUALFF, DataType.FLOAT, DataType.FLOAT),
            BinaryOperatorMapping(NCSInstructionType.NEQUALOO, DataType.OBJECT, DataType.OBJECT),
            BinaryOperatorMapping(NCSInstructionType.NEQUALSS, DataType.STRING, DataType.STRING),
        ])
        return t

    def t_GREATER_THAN_OR_EQUALS(self, t):
        '>\='
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.GEQII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.GEQFF, DataType.FLOAT, DataType.FLOAT),
        ])
        return t

    def t_GREATER_THAN(self, t):
        '>'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.GTII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.GTFF, DataType.FLOAT, DataType.FLOAT),
        ])
        return t

    def t_LESS_THAN_OR_EQUALS(self, t):
        '\<='
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.LEQII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.LEQFF, DataType.FLOAT, DataType.FLOAT),
        ])
        return t

    def t_LESS_THAN(self, t):
        '\<'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.LTII, DataType.INT, DataType.INT),
            BinaryOperatorMapping(NCSInstructionType.LTFF, DataType.FLOAT, DataType.FLOAT),
        ])
        return t

    def t_AND(self, t):
        '&&'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.LOGANDII, DataType.INT, DataType.INT),
        ])
        return t

    def t_OR(self, t):
        '\|\|'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.LOGORII, DataType.INT, DataType.INT),
        ])
        return t

    def t_NOT(self, t):
        '\!'
        t.value = OperatorMapping([
            UnaryOperatorMapping(NCSInstructionType.NOTI, DataType.INT),
        ], [])
        return t

    def t_BITWISE_AND(self, t):
        '&'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.BOOLANDII, DataType.INT, DataType.INT),
        ])
        return t

    def t_BITWISE_OR(self, t):
        '\|'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.INCORII, DataType.INT, DataType.INT),
        ])
        return t

    def t_BITWISE_XOR(self, t):
        '\^'
        t.value = OperatorMapping([], [
            BinaryOperatorMapping(NCSInstructionType.EXCORII, DataType.INT, DataType.INT),
        ])
        return t

    def t_BITWISE_NOT(self, t):
        '\~'
        t.value = OperatorMapping([UnaryOperatorMapping(NCSInstructionType.COMPI, DataType.INT)], [])
        return t
    # endregion
