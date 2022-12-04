from typing import List

from ply import yacc
from ply.yacc import YaccProduction

from pykotor.common.scriptdefs import KOTOR_FUNCTIONS, KOTOR_CONSTANTS

from pykotor.common.script import ScriptFunction, ScriptConstant

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import Identifier, IdentifierExpression, DeclarationStatement, \
    CodeBlock, \
    Statement, ScopedValue, AssignmentStatement, EngineCallExpression, Expression, ConditionalStatement, \
    FunctionDefinition, FunctionDefinitionParam, CodeRoot, AdditionExpression, SubtractionExpression
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self):
        self.parser = yacc.yacc(module=self)
        self.functions: List[ScriptFunction] = KOTOR_FUNCTIONS
        self.constants: List[ScriptConstant] = KOTOR_CONSTANTS

    tokens = NssLexer.tokens
    literals = NssLexer.literals

    def p_code_root(self, p):
        """
        code_root : code_root function_definition
                  | function_definition
                  |
        """
        if len(p) == 3:
            block: CodeRoot = p[1]
            block.functions.append(p[2])
            p[0] = block
        elif len(p) == 2:
            block = CodeRoot()
            block.functions.append(p[1])
            p[0] = block

    def p_function_definition(self, p):
        """
        function_definition : data_type IDENTIFIER '(' function_definition_params ')' '{' code_block '}'
        """
        p[0] = FunctionDefinition(p[1], p[2], p[4], p[7])
        p[7].build_parents()

    def p_function_definition_params(self, p):
        """
        function_definition_params : function_definition_params ',' data_type IDENTIFIER
                                   | data_type IDENTIFIER
                                   |
        """
        if len(p) == 5:
            params: List[FunctionDefinitionParam] = p[1]
            params.append(FunctionDefinitionParam(p[3], p[4]))
            p[0] = params
        elif len(p) == 3:
            params = []
            params.append(FunctionDefinitionParam(p[1], p[2]))
            p[0] = params
        elif len(p) == 1:
            p[0] =[]

    def p_code_block(self, p):
        """
        code_block : code_block statement
                   | statement
                   |
        """
        if len(p) == 3:
            block: CodeBlock = p[1]
            block.add(p[2])
            p[0] = block
        elif len(p) == 2:
            block = CodeBlock()
            block.add(p[1])
            p[0] = block
        elif len(p) == 1:
            p[0] = CodeBlock()

    def p_statement(self, p):
        """
        statement : ';'
                  | declaration_statement
                  | assignment_statement
                  | condition_statement
                  | expression ';'
        """
        p[0] = p[1]
        p[0].linenum = p.lineno(1)

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

    def p_condition_statement(self, p):
        """
        condition_statement : IF_CONTROL '(' expression ')' '{' code_block '}'
        """
        p[0] = ConditionalStatement(p[3], p[6])

    def p_add_expression(self, p):
        """
        add_expression : expression ADDITION_OPERATOR expression
        """
        p[0] = AdditionExpression(p[1], p[3])

    def p_subtract_expression(self, p):
        """
        subtract_expression : expression SUBTRACTION_OPERATOR expression
        """
        p[0] = SubtractionExpression(p[1], p[3])

    def p_expression(self, p):
        """
        expression : function_call
                   | INT_VALUE
                   | FLOAT_VALUE
                   | STRING_VALUE
                   | IDENTIFIER
                   | add_expression
                   | subtract_expression
        """
        if isinstance(p[1], Identifier):
            p[0] = IdentifierExpression(p[1])
        else:
            p[0] = p[1]

    def p_function_call(self, p):
        """
        function_call : IDENTIFIER '(' function_call_params ')'
        """
        identifier = p[1]
        engine_function = next((x for x in self.functions if x.name == identifier), None)
        if engine_function is not None:
            routine_id = self.functions.index(engine_function)
            data_type = engine_function.returntype
            args: List[Expression] = p[3]
            expression = EngineCallExpression(engine_function, routine_id, data_type, args)
            p[0] = expression

    def p_function_call_params(self, p):
        """
        function_call_params : function_call_params ',' expression
                             | expression
                             |
        """
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 1:
            p[0] = []

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

