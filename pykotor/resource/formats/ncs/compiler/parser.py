from ply import yacc


class NssParser:
    def __init__(self):
        self.parser = yacc.yacc(module=self)
