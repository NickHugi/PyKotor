from typing import List, Dict

from ply import yacc
from ply.yacc import YaccProduction

from pykotor.common.scriptdefs import KOTOR_FUNCTIONS, KOTOR_CONSTANTS

from pykotor.common.script import ScriptFunction, ScriptConstant
from pykotor.common.scriptlib import KOTOR_LIBRARY

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import Identifier, IdentifierExpression, InitializationStatement, \
    CodeBlock, \
    Statement, ScopedValue, Assignment, EngineCallExpression, Expression, ConditionalBlock, \
    FunctionDefinition, FunctionDefinitionParam, CodeRoot, UnaryOperatorExpression, BitwiseNotExpression, \
    LogicalNotExpression, IncludeScript, ReturnStatement, AdditionAssignment, ExpressionStatement, \
    SubtractionAssignment, MultiplicationAssignment, DivisionAssignment, EmptyStatement, WhileLoopBlock, \
    DoWhileLoopBlock, ForLoopBlock, FunctionCallExpression, FunctionForwardDeclaration, GlobalVariableDeclaration, \
    SwitchLabel, SwitchBlock, SwitchStatement, BreakStatement, ContinueStatement, ExpressionSwitchLabel, \
    DefaultSwitchLabel, ConditionAndBlock, BinaryOperatorExpression, StructDefinition, DeclarationStatement, \
    StructMember, DynamicDataType, FieldAccess, FieldAccessExpression
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer


class NssParser:
    def __init__(self, errorlog=yacc.NullLogger()):
        self.parser = yacc.yacc(module=self,
                               #errorlog=errorlog
                                )
        self.functions: List[ScriptFunction] = KOTOR_FUNCTIONS
        self.constants: List[ScriptConstant] = KOTOR_CONSTANTS
        self.library: Dict[str, str] = KOTOR_LIBRARY

    tokens = NssLexer.tokens
    literals = NssLexer.literals

    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'BITWISE_OR'),
        ('left', 'BITWISE_XOR'),
        ('left', 'BITWISE_AND'),
        ('left', 'EQUALS', 'NOT_EQUALS'),
        ('left', 'GREATER_THAN', 'LESS_THAN', 'GREATER_THAN_OR_EQUALS', 'LESS_THAN_OR_EQUALS'),
        ('left', 'BITWISE_LEFT', 'BITWISE_RIGHT'),
        ('left', 'ADD', 'MINUS', 'BITWISE_NOT'),
        ('left', 'MULTIPLY', 'DIVIDE', 'MOD'),
        ('left', 'BITWISE_NOT', 'NOT'),
        #('left', 'INCREMENT', 'DECREMENT'),
    )

    def p_code_root(self, p):
        """
        code_root : code_root function_definition
                  | code_root struct_definition
                  | code_root include_script
                  | code_root function_forward_declaration
                  | code_root global_variable_declaration
                  | function_definition
                  | include_script
                  | function_forward_declaration
                  | global_variable_declaration
                  | struct_definition
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

    def p_struct_definition(self, p):
        """
        struct_definition : STRUCT IDENTIFIER '{' struct_members '}' ';'
        """
        p[0] = StructDefinition(p[2], p[4])

    def p_struct_members(self, p):
        """
        struct_members : struct_members struct_member
                       |
        """
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_struct_member(self, p):
        """
        struct_member : data_type IDENTIFIER ';'
        """
        p[0] = StructMember(p[1], p[2])

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
                  | initialization_statement
                  | declaration_statement
                  | condition_statement
                  | return_statement
                  | while_loop
                  | do_while_loop
                  | for_loop
                  | switch_statement
                  | break_statement
                  | continue_statement
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

    def p_continue_statement(self, p):
        """
        continue_statement : CONTINUE_CONTROL ';'
        """
        p[0] = ContinueStatement()

    def p_initialization_statement(self, p):
        """
        initialization_statement : data_type IDENTIFIER '=' expression ';'
        """
        p[0] = InitializationStatement(p[2], p[1], p[4])

    def p_declaration_statement(self, p):
        """
        declaration_statement : data_type IDENTIFIER ';'
        """
        p[0] = DeclarationStatement(p[2], p[1])

    def p_normal_assignment(self, p):
        """
        assignment : field_access '=' expression
        """
        p[0] = Assignment(p[1], p[3])

    def p_addition_assignment(self, p):
        """
        assignment : field_access ADDITION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = AdditionAssignment(p[1], p[3])

    def p_subtraction_assignment(self, p):
        """
        assignment : field_access SUBTRACTION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = SubtractionAssignment(p[1], p[3])

    def p_multiplication_assignment(self, p):
        """
        assignment : field_access MULTIPLICATION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = MultiplicationAssignment(p[1], p[3])

    def p_division_assignment(self, p):
        """
        assignment : field_access DIVISION_ASSIGNMENT_OPERATOR expression
        """
        p[0] = DivisionAssignment(p[1], p[3])

    # region If Statement
    def p_condition_statement(self, p):
        """
        condition_statement : if_statement else_if_statements else_statement
        """
        p[0] = ConditionalBlock(p[1], p[2], p[3])
        # IF_CONTROL '(' expression ')' '{' code_block '}'
        # p[0] = ConditionalBlock(p[3], p[6])

    def p_if_statement(self, p):
        """
        if_statement : IF_CONTROL '(' expression ')' '{' code_block '}'
        """
        p[0] = ConditionAndBlock(p[3], p[6])

    def p_else_statement(self, p):
        """
        else_statement : ELSE_CONTROL '{' code_block '}'
                       |
        """
        if len(p) == 1:
            p[0] = None
        else:
            p[0] = p[3]

    def p_else_if_statement(self, p):
        """
        else_if_statement : ELSE_CONTROL IF_CONTROL '(' expression ')' '{' code_block '}'
        """
        p[0] = ConditionAndBlock(p[4], p[7])

    def p_else_if_statements(self, p):
        """
        else_if_statements : else_if_statements else_if_statement
                           |
        """
        if len(p) == 1:
            p[0] = []
        else:
            p[1].append(p[2])
            p[0] = p[1]

    # endregion

    def p_parenthesis_expression(self, p):
        """
        expression : '(' expression ')'
        """
        p[0] = p[2]

    def p_binary_operator(self, p):
        """
        expression : expression GREATER_THAN expression
                   | expression GREATER_THAN_OR_EQUALS expression
                   | expression LESS_THAN expression
                   | expression LESS_THAN_OR_EQUALS expression
                   | expression NOT_EQUALS expression
                   | expression EQUALS expression
                   | expression AND expression
                   | expression OR expression
                   | expression ADD expression
                   | expression MINUS expression
                   | expression MULTIPLY expression
                   | expression DIVIDE expression
                   | expression BITWISE_OR expression
                   | expression BITWISE_XOR expression
                   | expression BITWISE_AND expression
                   | expression BITWISE_LEFT expression
                   | expression BITWISE_RIGHT expression
                   | expression MOD expression
        """
        p[0] = BinaryOperatorExpression(p[1], p[3], p[2].binary)

    def p_unary_expression(self, p):
        """
        expression : MINUS expression
                   | BITWISE_NOT expression
                   | NOT expression
        """
        p[0] = UnaryOperatorExpression(p[2], p[1].unary)

    def p_return_statement(self, p):
        """
        return_statement : RETURN ';'
                         | RETURN expression ';'
        """
        if len(p) == 3:
            p[0] = ReturnStatement()
        elif len(p) == 4:
            p[0] = ReturnStatement(p[2])

    def p_expression(self, p):
        """
        expression : function_call
                   | INT_VALUE
                   | FLOAT_VALUE
                   | STRING_VALUE
                   | IDENTIFIER
                   | assignment
        """
        if isinstance(p[1], Identifier):
            p[0] = IdentifierExpression(p[1])
        else:
            p[0] = p[1]

    def p_field_access_expression(self, p):
        """
        expression : field_access
        """
        p[0] = FieldAccessExpression(p[1])

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
                  | STRUCT IDENTIFIER
        """
        if len(p) == 3:
            p[0] = DynamicDataType(p[1], p[2].label)
        else:
            p[0] = DynamicDataType(p[1])

    def p_field_access(self, p):
        """
        field_access : IDENTIFIER
                     | IDENTIFIER '.' IDENTIFIER
                     | field_access '.' IDENTIFIER
        """
        if len(p) == 2:
            p[0] = FieldAccess([p[1]])
        elif isinstance(p[1], Identifier):
            p[0] = FieldAccess([p[1], p[3]])
        else:
            p[0] = p[1]
            p[0].identifiers.append(p[3])

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

    def p_expression_switch_label(self, p):
        """
        switch_label : CASE_CONTROL expression ':'
        """
        p[0] = ExpressionSwitchLabel(p[2])

    def p_default_switch_label(self, p):
        """
        switch_label : DEFAULT_CONTROL ':'
        """
        p[0] = DefaultSwitchLabel()

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
    # endregion
