from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import AnalysisAdapter  # pyright: ignore[reportMissingImports]


class DestroyParseTree(AnalysisAdapter):
    def __init__(self):
        from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import AnalysisAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()

    def case_start(self, node):
        node.get_p_program().apply(self)
        node.set_p_program(None)

    def case_a_program(self, node):
        if node.get_size() is not None:
            node.get_size().apply(self)
        if node.get_conditional() is not None:
            node.get_conditional().apply(self)
        if node.get_jump_to_subroutine() is not None:
            node.get_jump_to_subroutine().apply(self)
        if node.get_return() is not None:
            node.get_return().apply(self)
        temp = list(node.get_subroutine())
        for i in range(len(temp)):
            temp[i].apply(self)
        node.set_size(None)
        node.set_conditional(None)
        node.set_jump_to_subroutine(None)
        node.set_return(None)
        from pykotor.resource.formats.ncs.dencs.node.vector import Vector  # pyright: ignore[reportMissingImports]
        node.set_subroutine(Vector(1))

    def case_a_subroutine(self, node):
        if node.get_command_block() is not None:
            node.get_command_block().apply(self)
        if node.get_return() is not None:
            node.get_return().apply(self)
        node.set_command_block(None)
        node.set_return(None)

    def case_a_command_block(self, node):
        temp = list(node.get_cmd())
        for i in range(len(temp)):
            temp[i].apply(self)
        from pykotor.resource.formats.ncs.dencs.node.vector import Vector  # pyright: ignore[reportMissingImports]
        node.set_cmd(Vector(1))

    def case_a_add_var_cmd(self, node):
        if node.get_rsadd_command() is not None:
            node.get_rsadd_command().apply(self)
        node.set_rsadd_command(None)

    def case_a_action_jump_cmd(self, node):
        if node.get_store_state_command() is not None:
            node.get_store_state_command().apply(self)
        if node.get_jump_command() is not None:
            node.get_jump_command().apply(self)
        if node.get_command_block() is not None:
            node.get_command_block().apply(self)
        if node.get_return() is not None:
            node.get_return().apply(self)
        node.set_store_state_command(None)
        node.set_jump_command(None)
        node.set_command_block(None)
        node.set_return(None)

    def case_a_const_cmd(self, node):
        if node.get_const_command() is not None:
            node.get_const_command().apply(self)
        node.set_const_command(None)

    def case_a_copydownsp_cmd(self, node):
        if node.get_copy_down_sp_command() is not None:
            node.get_copy_down_sp_command().apply(self)
        node.set_copy_down_sp_command(None)

    def case_a_copytopsp_cmd(self, node):
        if node.get_copy_top_sp_command() is not None:
            node.get_copy_top_sp_command().apply(self)
        node.set_copy_top_sp_command(None)

    def case_a_copydownbp_cmd(self, node):
        if node.get_copy_down_bp_command() is not None:
            node.get_copy_down_bp_command().apply(self)
        node.set_copy_down_bp_command(None)

    def case_a_copytopbp_cmd(self, node):
        if node.get_copy_top_bp_command() is not None:
            node.get_copy_top_bp_command().apply(self)
        node.set_copy_top_bp_command(None)

    def case_a_cond_jump_cmd(self, node):
        if node.get_conditional_jump_command() is not None:
            node.get_conditional_jump_command().apply(self)
        node.set_conditional_jump_command(None)

    def case_a_jump_cmd(self, node):
        if node.get_jump_command() is not None:
            node.get_jump_command().apply(self)
        node.set_jump_command(None)

    def case_a_jump_sub_cmd(self, node):
        if node.get_jump_to_subroutine() is not None:
            node.get_jump_to_subroutine().apply(self)
        node.set_jump_to_subroutine(None)

    def case_a_movesp_cmd(self, node):
        if node.get_move_sp_command() is not None:
            node.get_move_sp_command().apply(self)
        node.set_move_sp_command(None)

    def case_a_logii_cmd(self, node):
        if node.get_logii_command() is not None:
            node.get_logii_command().apply(self)
        node.set_logii_command(None)

    def case_a_unary_cmd(self, node):
        if node.get_unary_command() is not None:
            node.get_unary_command().apply(self)
        node.set_unary_command(None)

    def case_a_binary_cmd(self, node):
        if node.get_binary_command() is not None:
            node.get_binary_command().apply(self)
        node.set_binary_command(None)

    def case_a_destruct_cmd(self, node):
        if node.get_destruct_command() is not None:
            node.get_destruct_command().apply(self)
        node.set_destruct_command(None)

    def case_a_bp_cmd(self, node):
        if node.get_bp_command() is not None:
            node.get_bp_command().apply(self)
        node.set_bp_command(None)

    def case_a_action_cmd(self, node):
        if node.get_action_command() is not None:
            node.get_action_command().apply(self)
        node.set_action_command(None)

    def case_a_stack_op_cmd(self, node):
        if node.get_stack_command() is not None:
            node.get_stack_command().apply(self)
        node.set_stack_command(None)

    def case_a_return_cmd(self, node):
        if node.get_return() is not None:
            node.get_return().apply(self)
        node.set_return(None)

    def case_a_store_state_cmd(self, node):
        if node.get_store_state_command() is not None:
            node.get_store_state_command().apply(self)
        node.set_store_state_command(None)

    def case_a_conditional_jump_command(self, node):
        node.set_jump_if(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_semi(None)

    def case_a_jump_command(self, node):
        node.set_jmp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_semi(None)

    def case_a_jump_to_subroutine(self, node):
        node.set_jsr(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_semi(None)

    def case_a_return(self, node):
        node.set_retn(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_semi(None)

    def case_a_copy_down_sp_command(self, node):
        node.set_cpdownsp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_size(None)
        node.set_semi(None)

    def case_a_copy_top_sp_command(self, node):
        node.set_cptopsp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_size(None)
        node.set_semi(None)

    def case_a_copy_down_bp_command(self, node):
        node.set_cpdownbp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_size(None)
        node.set_semi(None)

    def case_a_copy_top_bp_command(self, node):
        node.set_cptopbp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_size(None)
        node.set_semi(None)

    def case_a_move_sp_command(self, node):
        node.set_movsp(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_semi(None)

    def case_a_rsadd_command(self, node):
        node.set_rsadd(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_semi(None)

    def case_a_const_command(self, node):
        node.set_const(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_constant(None)
        node.set_semi(None)

    def case_a_action_command(self, node):
        node.set_action(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_id(None)
        node.set_arg_count(None)
        node.set_semi(None)

    def case_a_logii_command(self, node):
        node.set_logii_op(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_semi(None)

    def case_a_binary_command(self, node):
        node.set_binary_op(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_size(None)
        node.set_semi(None)

    def case_a_unary_command(self, node):
        node.set_unary_op(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_semi(None)

    def case_a_stack_command(self, node):
        node.set_stack_op(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_offset(None)
        node.set_semi(None)

    def case_a_destruct_command(self, node):
        node.set_destruct(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_size_rem(None)
        node.set_offset(None)
        node.set_size_save(None)
        node.set_semi(None)

    def case_a_bp_command(self, node):
        node.set_bp_op(None)
        node.set_pos(None)
        node.set_type(None)
        node.set_semi(None)

    def case_a_store_state_command(self, node):
        node.set_storestate(None)
        node.set_pos(None)
        node.set_offset(None)
        node.set_size_bp(None)
        node.set_size_sp(None)
        node.set_semi(None)

