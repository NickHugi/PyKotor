from __future__ import annotations

from typing import ClassVar

from ply import lex

from pykotor.common.script import DataType
from pykotor.resource.formats.ncs import NCSInstructionType
from pykotor.resource.formats.ncs.compiler.classes import (
    BinaryOperatorMapping,
    ControlKeyword,
    FloatExpression,
    Identifier,
    IntExpression,
    ObjectExpression,
    OperatorMapping,
    StringExpression,
    UnaryOperatorMapping,
)


class NssLexer:
    def __init__(
        self,
        errorlog=lex.NullLogger(),  # noqa: B008
        *,
        nowarn=True,
    ):
        self.lexer: lex.Lexer = lex.lex(module=self, errorlog=errorlog, nowarn=nowarn)
        self.lexer.begin("INITIAL")

    tokens: ClassVar[list[str]] = [
        "STRING_VALUE",
        "INT_VALUE",
        "FLOAT_VALUE",
        "IDENTIFIER",
        "INT_TYPE",
        "INT_HEX_VALUE",
        "FLOAT_TYPE",
        "OBJECT_TYPE",
        "VOID_TYPE",
        "EVENT_TYPE",
        "EFFECT_TYPE",
        "ITEMPROPERTY_TYPE",
        "LOCATION_TYPE",
        "STRING_TYPE",
        "TALENT_TYPE",
        "VECTOR_TYPE",
        "ACTION_TYPE",
        "BREAK_CONTROL",
        "CASE_CONTROL",
        "DEFAULT_CONTROL",
        "DO_CONTROL",
        "ELSE_CONTROL",
        "SWITCH_CONTROL",
        "WHILE_CONTROL",
        "FOR_CONTROL",
        "IF_CONTROL",
        "TRUE_VALUE",
        "FALSE_VALUE",
        "OBJECTSELF_VALUE",
        "OBJECTINVALID_VALUE",
        "ADD",
        "MINUS",
        "MULTIPLY",
        "DIVIDE",
        "MOD",
        "EQUALS",
        "NOT_EQUALS",
        "GREATER_THAN",
        "LESS_THAN",
        "LESS_THAN_OR_EQUALS",
        "GREATER_THAN_OR_EQUALS",
        "AND",
        "OR",
        "NOT",
        "BITWISE_AND",
        "BITWISE_OR",
        "BITWISE_LEFT",
        "BITWISE_RIGHT",
        "BITWISE_XOR",
        "BITWISE_NOT",
        "INCLUDE",
        "RETURN",
        "ADDITION_ASSIGNMENT_OPERATOR",
        "SUBTRACTION_ASSIGNMENT_OPERATOR",
        "MULTIPLICATION_ASSIGNMENT_OPERATOR",
        "DIVISION_ASSIGNMENT_OPERATOR",
        "CONTINUE_CONTROL",
        "STRUCT",
        "INCREMENT",
        "DECREMENT",
        "NOP",
    ]

    literals: ClassVar[list[str]] = [
        "{",
        "}",
        "(",
        ")",
        ";",
        "=",
        ",",
        ":",
        ".",
        "[",
        "]",
    ]

    t_ignore: str = " \t\r"

    def t_NEWLINE(self, t):
        r"\n+"  # noqa: D300, D400, D415
        t.lexer.lineno += len(t.value)

    def t_NOP(self, t):
        "nop"  # noqa: D300, D400, D415, D403
        return t

    def t_COMMENT(self, t):
        r"//[^\n]*\n"  # noqa: D300, D400, D415
        t.lexer.lineno += 1

    def t_MULTILINE_COMMENT(self, t):
        r"\/\*(\*(?!\/)|[^*])*\*\/"  # noqa: D300, D400, D415
        t.lexer.lineno += t.value.count("\n")

    def t_INCLUDE(self, t):
        r"\#include"  # noqa: D300, D400, D415
        return t

    def t_OBJECTSELF_VALUE(self, t):
        r"OBJECT_SELF\b"  # noqa: D300, D400, D415
        t.value = ObjectExpression(0)
        return t

    def t_OBJECTINVALID_VALUE(self, t):
        r"OBJECT_INVALID\b"  # noqa: D300, D400, D415
        t.value = ObjectExpression(1)
        return t

    def t_TRUE_VALUE(self, t):
        r"TRUE\b"  # noqa: D300, D400, D415
        t.value = IntExpression(1)
        return t

    def t_FALSE_VALUE(self, t):
        r"FALSE\b"  # noqa: D300, D400, D415
        t.value = IntExpression(0)
        return t

    # region Control Tokens
    def t_BREAK_CONTROL(self, t):
        r"break\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.BREAK
        return t

    def t_CONTINUE_CONTROL(self, t):
        r"continue\b"  # noqa: D300, D400, D415
        return t

    def t_CASE_CONTROL(self, t):
        r"case\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.CASE
        return t

    def t_DEFAULT_CONTROL(self, t):
        r"default\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.DEFAULT
        return t

    def t_DO_CONTROL(self, t):
        r"do\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.DO
        return t

    def t_ELSE_CONTROL(self, t):
        r"else\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.ELSE
        return t

    def t_SWITCH_CONTROL(self, t):
        r"switch\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.SWITCH
        return t

    def t_WHILE_CONTROL(self, t):
        r"while\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.WHILE
        return t

    def t_FOR_CONTROL(self, t):
        r"for\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.FOR
        return t

    def t_IF_CONTROL(self, t):
        r"if\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.IF
        return t

    def t_RETURN(self, t):
        r"return\b"  # noqa: D300, D400, D415
        t.value = ControlKeyword.RETURN
        return t

    # endregion

    # region Type Tokens
    def t_STRUCT(self, t):
        r"struct\b"  # noqa: D300, D400, D415
        t.value = DataType.STRUCT
        return t

    def t_INT_TYPE(self, t):
        r"int\b"  # noqa: D300, D400, D415
        t.value = DataType.INT
        return t

    def t_FLOAT_TYPE(self, t):
        r"float\b"  # noqa: D300, D400, D415
        t.value = DataType.FLOAT
        return t

    def t_OBJECT_TYPE(self, t):
        r"object\b"  # noqa: D300, D400, D415
        t.value = DataType.OBJECT
        return t

    def t_VOID_TYPE(self, t):
        r"void\b"  # noqa: D300, D400, D415
        t.value = DataType.VOID
        return t

    def t_EVENT_TYPE(self, t):
        r"event\b"  # noqa: D300, D400, D415
        t.value = DataType.EVENT
        return t

    def t_EFFECT_TYPE(self, t):
        r"effect\b"  # noqa: D300, D400, D415
        t.value = DataType.EFFECT
        return t

    def t_ITEMPROPERTY_TYPE(self, t):
        r"itemproperty\b"  # noqa: D300, D400, D415
        t.value = DataType.ITEMPROPERTY
        return t

    def t_LOCATION_TYPE(self, t):
        r"location\b"  # noqa: D300, D400, D415
        t.value = DataType.LOCATION
        return t

    def t_STRING_TYPE(self, t):
        r"string\b"  # noqa: D300, D400, D415
        t.value = DataType.STRING
        return t

    def t_TALENT_TYPE(self, t):
        r"talent\b"  # noqa: D300, D400, D415
        t.value = DataType.TALENT
        return t

    def t_ACTION_TYPE(self, t):
        r"action\b"  # noqa: D300, D400, D415
        t.value = DataType.ACTION
        return t

    def t_VECTOR_TYPE(self, t):
        r"vector\b"  # noqa: D300, D400, D415
        t.value = DataType.VECTOR
        return t

    # endregion

    # region Value Tokens
    def t_IDENTIFIER(self, t):
        "[a-zA-Z_]+[a-zA-Z0-9_]*"  # noqa: D300, D400, D415
        t.value = Identifier(t.value)
        return t

    def t_STRING_VALUE(self, t):
        r"\"[^\"]*\" "  # noqa: D300, D400, D415, D210
        t.value = StringExpression(t.value[1:-1])
        return t

    def t_FLOAT_VALUE(self, t):
        r"[0-9]+\.[0-9]+f?|[0-9]f"  # noqa: D300, D400, D415
        t.value = FloatExpression(float(t.value.replace("f", "")))
        return t

    def t_INT_HEX_VALUE(self, t):
        "0x[0-9a-fA-F]+"  # noqa: D300, D400, D415
        t.value = IntExpression(int(t.value, 16))
        return t

    def t_INT_VALUE(self, t):
        "[0-9]+"  # noqa: D300, D400, D415
        t.value = IntExpression(int(t.value))
        return t

    # endregion

    def t_INCREMENT(self, t):
        r"\+\+"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[
                UnaryOperatorMapping(NCSInstructionType.INCISP, DataType.INT),
            ],
            binary=[],
        )
        return t

    def t_DECREMENT(self, t):
        r"\-\-"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[
                UnaryOperatorMapping(NCSInstructionType.DECISP, DataType.INT),
            ],
            binary=[],
        )
        return t

    def t_ADDITION_ASSIGNMENT_OPERATOR(self, t):
        r"\+\="  # noqa: D300, D400, D415
        return t

    def t_SUBTRACTION_ASSIGNMENT_OPERATOR(self, t):
        r"\-\="  # noqa: D300, D400, D415
        return t

    def t_MULTIPLICATION_ASSIGNMENT_OPERATOR(self, t):
        r"\*\="  # noqa: D300, D400, D415
        return t

    def t_DIVISION_ASSIGNMENT_OPERATOR(self, t):
        r"/\="  # noqa: D300, D400, D415
        return t

    # region Operators
    def t_BITWISE_LEFT(self, t):
        "<<"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.SHLEFTII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_BITWISE_RIGHT(self, t):
        ">>"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.SHRIGHTII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_ADD(self, t):
        r"\+"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.ADDII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.ADDIF, DataType.INT, DataType.INT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.ADDFI, DataType.FLOAT, DataType.FLOAT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.ADDFF, DataType.FLOAT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.ADDVV, DataType.VECTOR, DataType.VECTOR, DataType.VECTOR),
                BinaryOperatorMapping(NCSInstructionType.ADDSS, DataType.STRING, DataType.STRING, DataType.STRING),
            ],
        )
        return t

    def t_MINUS(self, t):
        "-"  # noqa: D300, D415, D400
        t.value = OperatorMapping(
            unary=[
                UnaryOperatorMapping(NCSInstructionType.NEGI, DataType.INT),
                UnaryOperatorMapping(NCSInstructionType.NEGF, DataType.FLOAT),
            ],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.SUBII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.SUBIF, DataType.INT, DataType.INT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.SUBFI, DataType.FLOAT, DataType.FLOAT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.SUBFF, DataType.FLOAT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.SUBVV, DataType.VECTOR, DataType.VECTOR, DataType.VECTOR),
            ],
        )
        return t

    def t_MULTIPLY(self, t):
        r"\*"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.MULII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.MULIF, DataType.INT, DataType.INT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.MULFI, DataType.FLOAT, DataType.FLOAT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.MULFF, DataType.FLOAT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.MULVF, DataType.VECTOR, DataType.VECTOR, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.MULFV, DataType.VECTOR, DataType.FLOAT, DataType.VECTOR),
            ],
        )
        return t

    def t_DIVIDE(self, t):
        "/"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.DIVII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.DIVIF, DataType.INT, DataType.INT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.DIVFI, DataType.FLOAT, DataType.FLOAT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.DIVFF, DataType.FLOAT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.DIVVF, DataType.VECTOR, DataType.VECTOR, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.DIVFV, DataType.VECTOR, DataType.FLOAT, DataType.VECTOR),
            ],
        )
        return t

    def t_MOD(self, t):
        r"\%"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.MODII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_EQUALS(self, t):
        r"\=\="  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.EQUALII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.EQUALFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.EQUALOO, DataType.INT, DataType.OBJECT, DataType.OBJECT),
                BinaryOperatorMapping(NCSInstructionType.EQUALSS, DataType.INT, DataType.STRING, DataType.STRING),
            ],
        )
        return t

    def t_NOT_EQUALS(self, t):
        r"\!="  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.NEQUALII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.NEQUALFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
                BinaryOperatorMapping(NCSInstructionType.NEQUALOO, DataType.INT, DataType.OBJECT, DataType.OBJECT),
                BinaryOperatorMapping(NCSInstructionType.NEQUALSS, DataType.INT, DataType.STRING, DataType.STRING),
            ],
        )
        return t

    def t_GREATER_THAN_OR_EQUALS(self, t):
        r">\="  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.GEQII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.GEQFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
            ],
        )
        return t

    def t_GREATER_THAN(self, t):
        ">"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.GTII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.GTFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
            ],
        )
        return t

    def t_LESS_THAN_OR_EQUALS(self, t):
        r"\<="  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.LEQII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.LEQFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
            ],
        )
        return t

    def t_LESS_THAN(self, t):
        r"\<"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.LTII, DataType.INT, DataType.INT, DataType.INT),
                BinaryOperatorMapping(NCSInstructionType.LTFF, DataType.INT, DataType.FLOAT, DataType.FLOAT),
            ],
        )
        return t

    def t_AND(self, t):
        "&&"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.LOGANDII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_OR(self, t):
        r"\|\|"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.LOGORII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_NOT(self, t):
        r"\!"  # noqa: D300, D400
        t.value = OperatorMapping(
            unary=[
                UnaryOperatorMapping(NCSInstructionType.NOTI, DataType.INT),
            ],
            binary=[],
        )
        return t

    def t_BITWISE_AND(self, t):
        "&"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.BOOLANDII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_BITWISE_OR(self, t):
        r"\|"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.INCORII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_BITWISE_XOR(self, t):
        r"\^"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[],
            binary=[
                BinaryOperatorMapping(NCSInstructionType.EXCORII, DataType.INT, DataType.INT, DataType.INT),
            ],
        )
        return t

    def t_BITWISE_NOT(self, t):
        r"\~"  # noqa: D300, D400, D415
        t.value = OperatorMapping(
            unary=[
                UnaryOperatorMapping(NCSInstructionType.COMPI, DataType.INT),
            ],
            binary=[],
        )
        return t

    # endregion
