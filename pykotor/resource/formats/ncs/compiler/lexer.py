from ply.lex import lex


class NssLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.lexer.begin("INTIAL")
