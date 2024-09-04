from __future__ import annotations

from typing import TYPE_CHECKING, Collection, NoReturn

from ply import yacc

from pykotor.resource.formats.ncs.compiler.classes import (
    AdditionAssignment,
    Assignment,
    BinaryOperatorExpression,
    BreakStatement,
    CodeBlock,
    CodeRoot,
    CompileError,
    ConditionAndBlock,
    ConditionalBlock,
    ContinueStatement,
    DeclarationStatement,
    DefaultSwitchLabel,
    DivisionAssignment,
    DoWhileLoopBlock,
    DynamicDataType,
    EmptyStatement,
    EngineCallExpression,
    ExpressionStatement,
    ExpressionSwitchLabel,
    FieldAccess,
    FieldAccessExpression,
    ForLoopBlock,
    FunctionCallExpression,
    FunctionDefinition,
    FunctionDefinitionParam,
    FunctionForwardDeclaration,
    GlobalVariableDeclaration,
    GlobalVariableInitialization,
    Identifier,
    IdentifierExpression,
    IncludeScript,
    MultiplicationAssignment,
    NopStatement,
    PostfixDecrementExpression,
    PostfixIncrementExpression,
    PrefixDecrementExpression,
    PrefixIncrementExpression,
    ReturnStatement,
    StructDefinition,
    StructMember,
    SubtractionAssignment,
    SwitchBlock,
    SwitchStatement,
    UnaryOperatorExpression,
    VariableDeclarator,
    VariableInitializer,
    VectorExpression,
    WhileLoopBlock,
)
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from utility.system.path import Path

if TYPE_CHECKING:
    from ply.lex import LexToken

    from pykotor.common.script import ScriptConstant, ScriptFunction
    from pykotor.resource.formats.ncs.compiler.classes import (
        Expression,
    )


class NssParser:
    def __init__(
        self,
        functions: list[ScriptFunction],
        constants: list[ScriptConstant],
        library: dict[str, bytes],
        library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None,
        errorlog: yacc.NullLogger | None = yacc.NullLogger(),  # noqa: B008
        debug: bool = False,
    ):
        self.parser: yacc.LRParser = yacc.yacc(
            module=self,
            errorlog=errorlog,
            write_tables=False,
            debug=debug,
        )
        self.functions: list[ScriptFunction] = functions
        self.constants: list[ScriptConstant] = constants
        self.library: dict[str, bytes] = library
        self.library_lookup: list[Path] = []
        if library_lookup:
            if not isinstance(library_lookup, list):
                library_lookup = [library_lookup]
            self.library_lookup = [Path.pathify(item) for item in library_lookup]

    tokens: list[str] = NssLexer.tokens
    literals: list[str] = NssLexer.literals

    precedence = (
        ("left", "OR"),
        ("left", "AND"),
        ("left", "BITWISE_OR"),
        ("left", "BITWISE_XOR"),
        ("left", "BITWISE_AND"),
        ("left", "EQUALS", "NOT_EQUALS"),
        ("left", "GREATER_THAN", "LESS_THAN", "GREATER_THAN_OR_EQUALS", "LESS_THAN_OR_EQUALS"),
        ("left", "BITWISE_LEFT", "BITWISE_RIGHT"),
        ("left", "ADD", "MINUS"),
        ("left", "MULTIPLY", "DIVIDE", "MOD"),
        ("right", "BITWISE_NOT", "NOT"),
        ("left", "INCREMENT", "DECREMENT"),
    )

    def p_error(self, p: LexToken) -> NoReturn:
        msg = f"Syntax error at line {p.lineno}, position {p.lexpos}, token='{p.value}'"
        raise CompileError(msg)

    def p_code_root(self, p: LexToken):
        """
        code_root : code_root code_root_object
                  |
        """  # noqa: D205, D415, D400, D212
        if len(p) == 3:
            p[1].objects.append(p[2])
            p[0] = p[1]
        else:
            p[0] = CodeRoot(
                constants=self.constants, functions=self.functions, library_lookup=self.library_lookup, library=self.library
            )

    def p_code_root_object(self, p):
        """
        code_root_object : function_definition
                         | include_script
                         | function_forward_declaration
                         | global_variable_declaration
                         | global_variable_initialization
                         | struct_definition
        """  # noqa: D205, D415, D400, D212
        p[0] = p[1]

    def p_struct_definition(self, p):
        """
        struct_definition : STRUCT IDENTIFIER '{' struct_members '}' ';'
        """  # noqa: D415, D400, D212, D200
        p[0] = StructDefinition(p[2], p[4])

    def p_struct_members(self, p):
        """
        struct_members : struct_members struct_member
                       |
        """  # noqa: D415, D400, D212, D205
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_struct_member(self, p):
        """
        struct_member : data_type IDENTIFIER ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = StructMember(p[1], p[2])

    def p_include_script(self, p):
        """
        include_script : INCLUDE STRING_VALUE
        """  # noqa: D200, D400, D212, D415
        p[0] = IncludeScript(p[2], library=self.library)

    def p_global_variable_initialization(self, p):
        """
        global_variable_initialization : data_type IDENTIFIER '=' expression ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = GlobalVariableInitialization(p[2], p[1], p[4])

    def p_global_variable_declaration(self, p):
        """
        global_variable_declaration : data_type IDENTIFIER ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = GlobalVariableDeclaration(p[2], p[1])

    def p_function_forward_declaration(self, p):
        """
        function_forward_declaration : data_type IDENTIFIER '(' function_definition_params ')' ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = FunctionForwardDeclaration(p[1], p[2], p[4])

    def p_function_definition(self, p):
        """
        function_definition : data_type IDENTIFIER '(' function_definition_params ')' '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = FunctionDefinition(p[1], p[2], p[4], p[7])

    def p_function_definition_params(self, p):
        """
        function_definition_params : function_definition_params ',' function_definition_param
                                   | function_definition_param
                                   |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        elif len(p) == 2:
            p[0] = [p[1]]
        elif len(p) == 1:
            p[0] = []

    def p_function_definition_param(self, p):
        """
        function_definition_param : data_type IDENTIFIER
        """  # noqa: D200, D400, D212, D415
        p[0] = FunctionDefinitionParam(p[1], p[2])

    def p_function_definition_param_with_default(self, p):
        """
        function_definition_param : data_type IDENTIFIER '=' expression
        """  # noqa: D200, D400, D212, D415
        p[0] = FunctionDefinitionParam(p[1], p[2], p[4])

    def p_code_block(self, p):
        """
        code_block : code_block statement
                   | statement
                   |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:
            block: CodeBlock = p[1]
            block.add(p[2])
            p[0] = block
        elif len(p) == 2:  # sourcery skip: class-extract-method
            block = CodeBlock()
            block.add(p[1])
            p[0] = block
        elif len(p) == 1:
            p[0] = CodeBlock()

    def p_while_loop(self, p):
        """
        while_loop : WHILE_CONTROL '(' expression ')' '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = WhileLoopBlock(p[3], p[6])

    def p_do_while_loop(self, p):
        """
        do_while_loop : DO_CONTROL '{' code_block '}' WHILE_CONTROL '(' expression ')' ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = DoWhileLoopBlock(p[7], p[3])

    def p_for_loop(self, p):
        """
        for_loop : FOR_CONTROL '(' expression ';' expression ';' expression ')' '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = ForLoopBlock(p[3], p[5], p[7], p[10])

    def p_scoped_block(self, p):
        """
        scoped_block : '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = p[2]

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
                  | continue_statement
                  | scoped_block
        """  # noqa: D400, D212, D415, D205
        if p[1] == ";":
            p[0] = EmptyStatement()
        else:
            p[0] = p[1]

    def p_nop_statement(self, p):
        """
        statement : NOP STRING_VALUE ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = NopStatement(p[2].value)

    def p_expression_statement(self, p):
        """
        statement : expression ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = ExpressionStatement(p[1])

    def p_break_statement(self, p):
        """
        break_statement : BREAK_CONTROL ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = BreakStatement()

    def p_continue_statement(self, p):
        """
        continue_statement : CONTINUE_CONTROL ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = ContinueStatement()

    def p_declaration_statement(self, p):
        """
        declaration_statement : data_type variable_declarators ';'
        """  # noqa: D200, D400, D212, D415
        p[0] = DeclarationStatement(p[1], p[2])

    def p_variable_declarators(self, p):
        """
        variable_declarators : variable_declarators ',' variable_declarator
                             | variable_declarator
        """  # noqa: D400, D212, D415, D205
        if len(p) == 4:
            p[1].append(p[3])
            p[0] = p[1]
        elif len(p) == 2:
            p[0] = [p[1]]

    def p_variable_declarator_no_initializer(self, p):
        """
        variable_declarator : IDENTIFIER
        """  # noqa: D200, D400, D212, D415
        p[0] = VariableDeclarator(p[1])

    def p_variable_declarator_initializer(self, p):
        """
        variable_declarator : IDENTIFIER '=' expression
        """  # noqa: D200, D400, D212, D415
        p[0] = VariableInitializer(p[1], p[3])

    def p_normal_assignment(self, p):
        """
        assignment : field_access '=' expression
        """  # noqa: D200, D400, D212, D415
        p[0] = Assignment(p[1], p[3])

    def p_addition_assignment(self, p):
        """
        assignment : field_access ADDITION_ASSIGNMENT_OPERATOR expression
        """  # noqa: D200, D400, D212, D415
        p[0] = AdditionAssignment(p[1], p[3])

    def p_subtraction_assignment(self, p):
        """
        assignment : field_access SUBTRACTION_ASSIGNMENT_OPERATOR expression
        """  # noqa: D200, D400, D212, D415
        p[0] = SubtractionAssignment(p[1], p[3])

    def p_multiplication_assignment(self, p):
        """
        assignment : field_access MULTIPLICATION_ASSIGNMENT_OPERATOR expression
        """  # noqa: D200, D400, D212, D415
        p[0] = MultiplicationAssignment(p[1], p[3])

    def p_division_assignment(self, p):
        """
        assignment : field_access DIVISION_ASSIGNMENT_OPERATOR expression
        """  # noqa: D200, D400, D212, D415
        p[0] = DivisionAssignment(p[1], p[3])

    # region If Statement
    def p_condition_statement(self, p):
        """
        condition_statement : if_statement else_if_statements else_statement
        """  # noqa: D200, D400, D212, D415
        p[0] = ConditionalBlock(p[1], p[2], p[3])
        # IF_CONTROL '(' expression ')' '{' code_block '}'

    def p_if_statement(self, p):
        """
        if_statement : IF_CONTROL '(' expression ')' '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = ConditionAndBlock(p[3], p[6])

    def p_if_statement_single(self, p):
        """
        if_statement : IF_CONTROL '(' expression ')' statement
        """  # noqa: D200, D400, D212, D415
        block = CodeBlock()
        block.add(p[5])
        p[0] = ConditionAndBlock(p[3], block)

    def p_else_statement(self, p):
        """
        else_statement : ELSE_CONTROL '{' code_block '}'
                       |
        """  # noqa: D400, D212, D415, D205
        p[0] = None if len(p) == 1 else p[3]

    def p_else_statement_single(self, p):
        """
        else_statement : ELSE_CONTROL statement
        """  # noqa: D200, D400, D212, D415
        block = CodeBlock()
        block.add(p[2])
        p[0] = block

    def p_else_if_statement(self, p):
        """
        else_if_statement : ELSE_CONTROL IF_CONTROL '(' expression ')' '{' code_block '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = ConditionAndBlock(p[4], p[7])

    def p_else_if_statement_single(self, p):
        """
        else_if_statement : ELSE_CONTROL IF_CONTROL '(' expression ')' statement
        """  # noqa: D200, D400, D212, D415
        block = CodeBlock()
        block.add(p[6])
        p[0] = ConditionAndBlock(p[4], block)

    def p_else_if_statements(self, p):
        """
        else_if_statements : else_if_statements else_if_statement
                           |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 1:
            p[0] = []
        else:
            p[1].append(p[2])
            p[0] = p[1]

    # endregion

    def p_parenthesis_expression(self, p):
        """
        expression : '(' expression ')'
        """  # noqa: D200, D400, D212, D415
        p[0] = p[2]

    def p_binary_operator(self, p):
        """
        expression : expression GREATER_THAN expression
                   | expression GREATER_THAN_OR_EQUALS expression
                   | expression LESS_THAN expression
                   | expression LESS_THAN_OR_EQUALS expression
                   | expression AND expression
                   | expression NOT_EQUALS expression
                   | expression EQUALS expression
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
        """  # noqa: D400, D212, D415, D205
        p[0] = BinaryOperatorExpression(p[1], p[3], p[2].binary)

    def p_unary_expression(self, p):
        """
        expression : MINUS expression
                   | BITWISE_NOT expression
                   | NOT expression
        """  # noqa: D400, D212, D415, D205
        p[0] = UnaryOperatorExpression(p[2], p[1].unary)

    def p_return_statement(self, p: Collection):
        """
        return_statement : RETURN ';'
                         | RETURN expression ';'
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:
            p[0] = ReturnStatement()
        elif len(p) == 4:
            p[0] = ReturnStatement(p[2])

    def p_expression(self, p):
        """
        expression : function_call
                   | IDENTIFIER
                   | assignment
                   | constant_expression
        """  # noqa: D400, D212, D415, D205
        p[0] = IdentifierExpression(p[1]) if isinstance(p[1], Identifier) else p[1]

    def p_constant_expression(self, p):
        """
        constant_expression : INT_VALUE
                            | FLOAT_VALUE
                            | STRING_VALUE
                            | OBJECTSELF_VALUE
                            | OBJECTINVALID_VALUE
                            | TRUE_VALUE
                            | FALSE_VALUE
                            | INT_HEX_VALUE
        """  # noqa: D400, D212, D415, D205
        p[0] = p[1]

    def p_field_access_expression(self, p):
        """
        expression : field_access
        """  # noqa: D200, D400, D212, D415
        p[0] = FieldAccessExpression(p[1])

    def p_function_call(self, p):
        """
        function_call : IDENTIFIER '(' function_call_params ')'
        """  # noqa: D200, D400, D212, D415
        identifier = p[1]
        args: list[Expression] = p[3]

        engine_function = next((x for x in self.functions if x.name == identifier), None)
        if engine_function:
            routine_id = self.functions.index(engine_function)
            data_type = engine_function.returntype
            p[0] = EngineCallExpression(engine_function, routine_id, data_type, args)
        else:
            args = p[3]
            p[0] = FunctionCallExpression(identifier, args)

    def p_function_call_params(self, p):
        """
        function_call_params : function_call_params ',' expression
                             | expression
                             |
        """  # noqa: D400, D212, D415, D205
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
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:  # noqa: PLR2004
            p[0] = DynamicDataType(p[1], p[2].label)
        else:
            p[0] = DynamicDataType(p[1])

    def p_field_access(self, p):
        """
        field_access : IDENTIFIER
                     | IDENTIFIER '.' IDENTIFIER
                     | field_access '.' IDENTIFIER
        """  # noqa: D400, D212, D415, D205
        if len(p) == 2:
            p[0] = FieldAccess([p[1]])
        elif isinstance(p[1], Identifier):
            p[0] = FieldAccess([p[1], p[3]])
        else:
            p[0] = p[1]
            p[0].identifiers.append(p[3])

    def p_prefix_increment_expression(self, p):
        """
        expression : INCREMENT field_access
        """  # noqa: D200, D400, D212, D415
        p[0] = PrefixIncrementExpression(p[2])

    def p_postfix_increment_expression(self, p):
        """
        expression : field_access INCREMENT
        """  # noqa: D200, D400, D212, D415
        p[0] = PostfixIncrementExpression(p[1])

    def p_prefix_decrement_expression(self, p):
        """
        expression : DECREMENT field_access
        """  # noqa: D200, D400, D212, D415
        p[0] = PrefixDecrementExpression(p[2])

    def p_postfix_decrement_expression(self, p):
        """
        expression : field_access DECREMENT
        """  # noqa: D200, D400, D212, D415
        p[0] = PostfixDecrementExpression(p[1])

    def p_vector_expression(self, p):
        """
        expression : '[' FLOAT_VALUE ',' FLOAT_VALUE ',' FLOAT_VALUE ']'
        """  # noqa: D200, D400, D212, D415
        p[0] = VectorExpression(p[2], p[4], p[6])

    # region Switch Statement
    def p_switch_statement(self, p):
        """
        switch_statement : SWITCH_CONTROL '(' expression ')' '{' switch_blocks '}'
        """  # noqa: D200, D400, D212, D415
        p[0] = SwitchStatement(p[3], p[6])

    def p_switch_blocks(self, p):
        """
        switch_blocks : switch_blocks switch_block
                      |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_switch_block(self, p):
        """
        switch_block : switch_labels block_statements
        """  # noqa: D200, D400, D212, D415
        p[0] = SwitchBlock(p[1], p[2])

    def p_switch_labels(self, p):
        """
        switch_labels : switch_labels switch_label
                      |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    def p_expression_switch_label(self, p):
        """
        switch_label : CASE_CONTROL expression ':'
        """  # noqa: D200, D400, D212, D415
        p[0] = ExpressionSwitchLabel(p[2])

    def p_default_switch_label(self, p):
        """
        switch_label : DEFAULT_CONTROL ':'
        """  # noqa: D200, D400, D212, D415
        p[0] = DefaultSwitchLabel()

    def p_block_statements(self, p):
        """
        block_statements : block_statements statement
                         |
        """  # noqa: D400, D212, D415, D205
        if len(p) == 3:
            p[1].append(p[2])
            p[0] = p[1]
        else:
            p[0] = []

    # endregion
