from ply import yacc

from pykotor.resource.formats.ncs.compiler.classes import Identifier, IdentifierValue, DeclarationStatement, CodeBlock
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self):
        self.parser = yacc.yacc(module=self)

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
            block.statements.append(p[2])
            p[0] = block
        elif len(p) == 2:
            block = CodeBlock()
            block.statements.append(p[1])
            p[0] = block
        elif len(p) == 1:
            ...

    def p_statement(self, p):
        """
        statement : ';'
                  | declaration_statement
        """
        p[0] = p[1]

    def p_declaration_statement(self, p):
        """
        declaration_statement : data_type IDENTIFIER '=' expression ';'
        """
        p[0] = DeclarationStatement(p[2], p[1], p[4])

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
