from ply import yacc

from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self):
        self.parser = yacc.yacc(module=self)

    tokens = NssLexer.tokens
    literals = NssLexer.literals


