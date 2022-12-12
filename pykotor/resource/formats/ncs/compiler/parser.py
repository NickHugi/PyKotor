from typing import List, Dict

from ply import yacc
from ply.yacc import YaccProduction

from pykotor.common.scriptdefs import KOTOR_FUNCTIONS, KOTOR_CONSTANTS

from pykotor.common.script import ScriptFunction, ScriptConstant
from pykotor.common.scriptlib import KOTOR_LIBRARY

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import Identifier, IdentifierExpression, DeclarationStatement, \
    CodeBlock, \
    Statement, ScopedValue, Assignment, EngineCallExpression, Expression, ConditionalBlock, \
    FunctionDefinition, FunctionDefinitionParam, CodeRoot, AdditionExpression, SubtractionExpression, \
    MultiplicationExpression, DivisionExpression, ModulusExpression, NegationExpression, BitwiseNotExpression, \
    LogicalNotExpression, LogicalAndExpression, LogicalOrExpression, BitwiseOrExpression, BitwiseXorExpression, \
    BitwiseAndExpression, LogicalEqualityExpression, LogicalInequalityExpression, GreaterThanExpression, \
    GreaterThanOrEqualExpression, LessThanExpression, LessThanOrEqualExpression, BitwiseLeftShiftExpression, \
    BitwiseRightShiftExpression, IncludeScript, ReturnStatement, AdditionAssignment, ExpressionStatement, \
    SubtractionAssignment, MultiplicationAssignment, DivisionAssignment, EmptyStatement, WhileLoopBlock, \
    DoWhileLoopBlock, ForLoopBlock, FunctionCallExpression, FunctionForwardDeclaration, GlobalVariableDeclaration, \
    SwitchLabel, SwitchBlock, SwitchStatement, BreakStatement
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self, errorlog=yacc.NullLogger()):
        self.parser = yacc.yacc(module=self,
                                errorlog=errorlog
                                )
        self.functions: List[ScriptFunction] = KOTOR_FUNCTIONS
        self.constants: List[ScriptConstant] = KOTOR_CONSTANTS
        self.library: Dict[str, str] = KOTOR_LIBRARY

    tokens = NssLexer.tokens
    literals = NssLexer.literals

    def p_code_root(self, p):
        """
        code_root : code_root function_definition
                  | code_root include_script
                  | code_root function_forward_declaration
                  | code_root global_variable_declaration
                  | function_definition
                  | include_script
                  | function_forward_declaration
                  | global_variable_declaration
                  |
        """
        if len(p) == 3:
            block: CodeRoot = p[1]
            p[0] = block
            block.objects.append(p[2])
        elif len(p) == 2:
            block = CodeRoot()
            p[0] = block
            block.objects.append(p[1])

    def p_include_script(self, p):
        """
        include_script : INCLUDE STRING_VALUE
        """
        p[0] = IncludeScript(p[2], library=self.library)

    def p_global_variable_declaration(self, p):
        """
        global_variable_declaration : data_type IDENTIFIER '=' expression ';'
        """
        p[0] = GlobalVariableDeclaration(p[2], p[1], p[4])

    def p_function_forward_declaration(self, p):
        """
        function_forward_declaration : data_type IDENTIFIER '(' function_definition_params ')' ';'
        """
        p[0] = FunctionForwardDeclaration(p[1], p[2], p[4])

    def p_function_definition(self, p):
        """
        function_definition : data_type IDENTIFIER '(' function_definition_params ')' '{' code_block '}'
        """
        p[0] = FunctionDefinition(p[1], p[2], p[4], p[7])

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

    def p_while_loop(self, p):
        """
        while_loop : WHILE_CONTROL '(' expression ')' '{' code_block '}'
        """
        p[0] = WhileLoopBlock(p[3], p[6])

    def p_do_while_loop(self, p):
        """
        do_while_loop : DO_CONTROL '{' code_block '}' WHILE_CONTROL '(' expression ')' ';'
        """
        p[0] = DoWhileLoopBlock(p[7], p[3])

    def p_for_loop(self, p):
        """
        for_loop : FOR_CONTROL '(' expression ';' expression ';' expression ')' '{' code_block '}'
        """
        p[0] = ForLoopBlock(p[3], p[5], p[7], p[10])

    def p_statement(self, p):
        """
        statement : ';'
                  | declaration_statement
                  | condition_statement
                  | return_statement
                  | while_loop
                  | do_while_loop
                  | for_loop
                  | switch_statement
                  | break_statement
                  | expression ';'
        """
        if isinstance(p[1], Expression):
            p[0] = ExpressionStatement(p[1])
        elif p[1] == ";":
            p[0] = EmptyStatement()
        else:
            p[0] = p[1]
        #p[0].linenum = p.lineno(1)

    def p_break_statement(self, p):
        """
        break_statement : BREAK_CONTROL ';'
        """
        p[0] = BreakStatement()

    def p_declaration_statement(self, p):
        """
        declaration_statement : data_type IDENTIFIER '=' expression ';'
        """
        p[0] = DeclarationStatement(p[2], p[1], p[4])

    def p_assignment(self, p):
        """
        assignment : IDENTIFIER '=' expression
        """
        p[0] = Assignment(p[1], p[3])

    def p_addition_assignment(self, p):
        """
        addition_assignment : IDENTIFIER ADDITION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = AdditionAssignment(p[1], p[3])

    def p_subtraction_assignment(self, p):
        """
        subtraction_assignment : IDENTIFIER SUBTRACTION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = SubtractionAssignment(p[1], p[3])

    def p_multiplication_assignment(self, p):
        """
        multiplication_assignment : IDENTIFIER MULTIPLICATION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = MultiplicationAssignment(p[1], p[3])

    def p_division_assignment(self, p):
        """
        division_assignment : IDENTIFIER DIVISION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = DivisionAssignment(p[1], p[3])

    def p_condition_statement(self, p):
        """
        condition_statement : IF_CONTROL '(' expression ')' '{' code_block '}'
        """
        p[0] = ConditionalBlock(p[3], p[6])

    def p_return_statement(self, p):
        """
        return_statement : RETURN ';'
                         | RETURN expression ';'
        """
        if len(p) == 3:
            p[0] = ReturnStatement()
        elif len(p) == 4:
            p[0] = ReturnStatement(p[2])

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

    def p_multiply_expression(self, p):
        """
        multiply_expression : expression MULTIPLY_OPERATOR expression
        """
        p[0] = MultiplicationExpression(p[1], p[3])

    def p_divide_expression(self, p):
        """
        divide_expression : expression DIVIDE_OPERATOR expression
        """
        p[0] = DivisionExpression(p[1], p[3])

    def p_modulus_expression(self, p):
        """
        modulus_expression : expression MODULUS_OPERATOR expression
        """
        p[0] = ModulusExpression(p[1], p[3])

    def p_negation_expression(self, p):
        """
        modulus_expression : SUBTRACTION_OPERATOR expression
        """
        p[0] = NegationExpression(p[2])

    def p_logical_not_expression(self, p):
        """
        logical_not_expression : NOT_OPERATOR expression
        """
        p[0] = LogicalNotExpression(p[2])

    def p_logical_and_expression(self, p):
        """
        logical_and_expression : expression AND_OPERATOR expression
        """
        p[0] = LogicalAndExpression(p[1], p[3])

    def p_logical_or_expression(self, p):
        """
        logical_or_expression : expression OR_OPERATOR expression
        """
        p[0] = LogicalOrExpression(p[1], p[3])

    def p_logical_equality_expression(self, p):
        """
        logical_equality_expression : expression EQUAL_OPERATOR expression
        """
        p[0] = LogicalEqualityExpression(p[1], p[3])

    def p_logical_inequality_expression(self, p):
        """
        logical_inequality_expression : expression NOT_EQUAL_OPERATOR expression
        """
        p[0] = LogicalInequalityExpression(p[1], p[3])

    def p_compare_greaterthan_expression(self, p):
        """
        compare_greaterthan_expression : expression GREATER_THAN_OPERATOR expression
        """
        p[0] = GreaterThanExpression(p[1], p[3])

    def p_compare_greaterthanorequal_expression(self, p):
        """
        compare_greaterthanorequal_expression : expression GREATER_THAN_OR_EQUAL_OPERATOR expression
        """
        p[0] = GreaterThanOrEqualExpression(p[1], p[3])

    def p_compare_lessthan_expression(self, p):
        """
        compare_lessthan_expression : expression LESS_THAN_OPERATOR expression
        """
        p[0] = LessThanExpression(p[1], p[3])

    def p_compare_lessthanorequal_expression(self, p):
        """
        compare_lessthanorequal_expression : expression LESS_THAN_OR_EQUAL_OPERATOR expression
        """
        p[0] = LessThanOrEqualExpression(p[1], p[3])

    def p_bitwise_or_expression(self, p):
        """
        bitwise_or_expression : expression BITWISE_OR_OPERATOR expression
        """
        p[0] = BitwiseOrExpression(p[1], p[3])

    def p_bitwise_xor_expression(self, p):
        """
        bitwise_xor_expression : expression BITWISE_XOR_OPERATOR expression
        """
        p[0] = BitwiseXorExpression(p[1], p[3])

    def p_bitwise_and_expression(self, p):
        """
        bitwise_and_expression : expression BITWISE_AND_OPERATOR expression
        """
        p[0] = BitwiseAndExpression(p[1], p[3])

    def p_bitwise_not_expression(self, p):
        """
        bitwise_not_expression : ONES_COMPLEMENT_OPERATOR expression
        """
        p[0] = BitwiseNotExpression(p[2])

    def p_bitwise_leftshift_expression(self, p):
        """
        bitwise_leftshift_expression : expression BITWISE_LEFT_OPERATOR expression
        """
        p[0] = BitwiseLeftShiftExpression(p[1], p[3])

    def p_bitwise_rightshift_expression(self, p):
        """
        bitwise_rightshift_expression : expression BITWISE_RIGHT_OPERATOR expression
        """
        p[0] = BitwiseRightShiftExpression(p[1], p[3])

    def p_expression(self, p):
        """
        expression : function_call
                   | INT_VALUE
                   | FLOAT_VALUE
                   | STRING_VALUE
                   | IDENTIFIER
                   | assignment
                   | addition_assignment
                   | subtraction_assignment
                   | multiplication_assignment
                   | division_assignment
                   | add_expression
                   | subtract_expression
                   | multiply_expression
                   | divide_expression
                   | modulus_expression
                   | bitwise_not_expression
                   | bitwise_or_expression
                   | bitwise_xor_expression
                   | bitwise_and_expression
                   | bitwise_leftshift_expression
                   | bitwise_rightshift_expression
                   | logical_not_expression
                   | logical_and_expression
                   | logical_or_expression
                   | logical_equality_expression
                   | logical_inequality_expression
                   | compare_greaterthan_expression
                   | compare_greaterthanorequal_expression
                   | compare_lessthan_expression
                   | compare_lessthanorequal_expression
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
        args: List[Expression] = p[3]

        if engine_function := next((x for x in self.functions if x.name == identifier), None):
            routine_id = self.functions.index(engine_function)
            data_type = engine_function.returntype
            p[0] = EngineCallExpression(engine_function, routine_id, data_type, args)
        else:
            args: List[Expression] = p[3]
            p[0] = FunctionCallExpression(identifier, args)

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

    # region Switch Statement
    def p_switch_statement(self, p):
        """
        switch_statement : SWITCH_CONTROL '(' expression ')' '{' switch_blocks '}'
        """
        p[0] = SwitchStatement(p[3], p[6])

    def p_switch_blocks(self, p):
        """
        switch_blocks : switch_blocks switch_block
                      |
        """
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_switch_block(self, p):
        """
        switch_block : switch_labels block_statements
        """
        p[0] = SwitchBlock(p[1], p[2])

    def p_switch_labels(self, p):
        """
        switch_labels : switch_labels switch_label
                      |
        """
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_switch_label(self, p):
        """
        switch_label : CASE_CONTROL expression ':'
        """
        p[0] = SwitchLabel(p[2])

    # endregion

    def p_block_statements(self, p):
        """
        block_statements : block_statements statement
                         |
        """
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []
