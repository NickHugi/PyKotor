from typing import List

from ply import yacc

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import Identifier, IdentifierValue, DeclarationStatement, CodeBlock, \
    Statement, ScopedValue, AssignmentStatement
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self):
        self.parser = yacc.yacc(module=self)
        self.ncs: NCS = NCS()

    tokens = NssLexer.tokens
    literals = NssLexer.literals

    def p_code_block(self, p):
        """
        code_block : code_block statement
                   | statement
                   |
        """
        if len(p) == 3:
            block: CodeBlock = p[1]
            statement: Statement = p[2]
            statement.compile(self.ncs, block)
            p[0] = block
        elif len(p) == 2:
            block = CodeBlock()
            statement: Statement = p[1]
            statement.compile(self.ncs, block)
            p[0] = block
        elif len(p) == 1:
            ...

    def p_statement(self, p):
        """
        statement : ';'
                  | declaration_statement
                  | assignment_statement
        """
        p[0] = p[1]

    def p_declaration_statement(self, p):
        """
        declaration_statement : data_type IDENTIFIER '=' expression ';'
        """
        p[0] = DeclarationStatement(p[2], p[1], p[4])

    def p_assignment_statement(self, p):
        """
        assignment_statement : IDENTIFIER '=' expression ';'
        """
        p[0] = AssignmentStatement(p[1], p[3])

    def p_expression(self, p):
        """
        expression : INT_VALUE
                   | FLOAT_VALUE
                   | STRING_VALUE
                   | IDENTIFIER
        """
        if isinstance(p[1], Identifier):
            p[0] = IdentifierValue(p[1])
        else:
            p[0] = p[1]

    def p_data_type(self, p):
        """
        data_type : INT_TYPE
                  | FLOAT_TYPE
                  | OBJECT_TYPE
                  | VOID_TYPE
                  | EVENT_TYPE
                  | EFFECT_TYPE
                  | ITEMPROPERTY_TYPE
                  | LOCATION_TYPE
                  | STRING_TYPE
                  | TALENT_TYPE
                  | VECTOR_TYPE
                  | ACTION_TYPE
        """
        p[0] = p[1]
