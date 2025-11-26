from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.actions_data import ActionsData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]


class NodeUtils:
    CMDSIZE_JUMP = 6
    CMDSIZE_RETN = 2

    @staticmethod
    def is_store_stack_node(node: Node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_logii_cmd import ALogiiCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_or_logii_op import AOrLogiiOp  # pyright: ignore[reportMissingImports]
        if isinstance(node, ALogiiCmd):
            lnode: ALogiiCommand = node.get_logii_command()
            if isinstance(lnode.get_logii_op(), AOrLogiiOp):
                return False
        return True

    @staticmethod
    def is_jz_past_one(node: Node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_zero_jump_if import AZeroJumpIf  # pyright: ignore[reportMissingImports]
        return isinstance(node, AConditionalJumpCommand) and isinstance(node.get_jump_if(), AZeroJumpIf) and int(node.get_offset().get_text()) == 12

    @staticmethod
    def is_jz(node: Node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_zero_jump_if import AZeroJumpIf  # pyright: ignore[reportMissingImports]
        return isinstance(node, AConditionalJumpCommand) and isinstance(node.get_jump_if(), AZeroJumpIf)

    @staticmethod
    def is_command_node(node: Node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
        return isinstance(node, (AConditionalJumpCommand, AJumpCommand, AJumpToSubroutine, AReturn,
                                ACopyDownSpCommand, ACopyTopSpCommand, ACopyDownBpCommand, ACopyTopBpCommand,
                                AMoveSpCommand, ARsaddCommand, AConstCommand, AActionCommand, ALogiiCommand,
                                ABinaryCommand, AUnaryCommand, AStackCommand, ADestructCommand, ABpCommand,
                                AStoreStateCommand))

    @staticmethod
    def get_command_pos(node: Node) -> int:
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
        if isinstance(node, AConditionalJumpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AJumpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AJumpToSubroutine):
            return int(node.get_pos().get_text())
        if isinstance(node, AReturn):
            return int(node.get_pos().get_text())
        if isinstance(node, ACopyDownSpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ACopyTopSpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ACopyDownBpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ACopyTopBpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AMoveSpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ARsaddCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AConstCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AActionCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ALogiiCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ABinaryCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AUnaryCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AStackCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ADestructCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, ABpCommand):
            return int(node.get_pos().get_text())
        if isinstance(node, AStoreStateCommand):
            return int(node.get_pos().get_text())
        return -1

    @staticmethod
    def get_jump_destination_pos(node: Node) -> int:
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        if isinstance(node, AConditionalJumpCommand):
            return int(node.get_pos().get_text()) + int(node.get_offset().get_text())
        if isinstance(node, AJumpCommand):
            return int(node.get_pos().get_text()) + int(node.get_offset().get_text())
        if isinstance(node, AJumpToSubroutine):
            return int(node.get_pos().get_text()) + int(node.get_offset().get_text())
        return -1

    @staticmethod
    def is_equality_op(node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_equal_binary_op import AEqualBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_nequal_binary_op import ANequalBinaryOp  # pyright: ignore[reportMissingImports]
        if not isinstance(node, ABinaryCommand):
            return False
        op = node.get_binary_op()
        return isinstance(op, (AEqualBinaryOp, ANequalBinaryOp))

    @staticmethod
    def is_conditional_op(node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_equal_binary_op import AEqualBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_nequal_binary_op import ANequalBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_lt_binary_op import ALtBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_leq_binary_op import ALeqBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_gt_binary_op import AGtBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_geq_binary_op import AGeqBinaryOp  # pyright: ignore[reportMissingImports]
        if not isinstance(node, ABinaryCommand):
            return False
        op = node.get_binary_op()
        return isinstance(op, (AEqualBinaryOp, ANequalBinaryOp, ALtBinaryOp, ALeqBinaryOp, AGtBinaryOp, AGeqBinaryOp))

    @staticmethod
    def is_arithmetic_op(node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_add_binary_op import AAddBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_sub_binary_op import ASubBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_div_binary_op import ADivBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_mul_binary_op import AMulBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_mod_binary_op import AModBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_shleft_binary_op import AShleftBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_shright_binary_op import AShrightBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unright_binary_op import AUnrightBinaryOp  # pyright: ignore[reportMissingImports]
        if not isinstance(node, ABinaryCommand):
            return False
        op = node.get_binary_op()
        return isinstance(op, (AAddBinaryOp, ASubBinaryOp, ADivBinaryOp, AMulBinaryOp, AModBinaryOp,
                              AShleftBinaryOp, AShrightBinaryOp, AUnrightBinaryOp))

    @staticmethod
    def is_vector_allowed_op(node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_add_binary_op import AAddBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_sub_binary_op import ASubBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_div_binary_op import ADivBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_mul_binary_op import AMulBinaryOp  # pyright: ignore[reportMissingImports]
        if not isinstance(node, ABinaryCommand):
            return False
        op = node.get_binary_op()
        return isinstance(op, (AAddBinaryOp, ASubBinaryOp, ADivBinaryOp, AMulBinaryOp))

    @staticmethod
    def get_op(node) -> str:
        from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_neg_unary_op import ANegUnaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_comp_unary_op import ACompUnaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_not_unary_op import ANotUnaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_add_binary_op import AAddBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_sub_binary_op import ASubBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_div_binary_op import ADivBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_mul_binary_op import AMulBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_mod_binary_op import AModBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_shleft_binary_op import AShleftBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_shright_binary_op import AShrightBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unright_binary_op import AUnrightBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_equal_binary_op import AEqualBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_nequal_binary_op import ANequalBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_lt_binary_op import ALtBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_leq_binary_op import ALeqBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_gt_binary_op import AGtBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_geq_binary_op import AGeqBinaryOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_and_logii_op import AAndLogiiOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_or_logii_op import AOrLogiiOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_incl_or_logii_op import AInclOrLogiiOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_excl_or_logii_op import AExclOrLogiiOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_bit_and_logii_op import ABitAndLogiiOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_decisp_stack_op import ADecispStackOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_decibp_stack_op import ADecibpStackOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_incisp_stack_op import AIncispStackOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_incibp_stack_op import AIncibpStackOp  # pyright: ignore[reportMissingImports]
        if isinstance(node, AUnaryCommand):
            op = node.get_unary_op()
            if isinstance(op, ANegUnaryOp):
                return "-"
            if isinstance(op, ACompUnaryOp):
                return "~"
            if isinstance(op, ANotUnaryOp):
                return "!"
            raise RuntimeError("unknown unary op")
        if isinstance(node, ABinaryCommand):
            op = node.get_binary_op()
            if isinstance(op, AAddBinaryOp):
                return "+"
            if isinstance(op, ASubBinaryOp):
                return "-"
            if isinstance(op, ADivBinaryOp):
                return "/"
            if isinstance(op, AMulBinaryOp):
                return "*"
            if isinstance(op, AModBinaryOp):
                return "%"
            if isinstance(op, AShleftBinaryOp):
                return "<<"
            if isinstance(op, AShrightBinaryOp):
                return ">>"
            if isinstance(op, AUnrightBinaryOp):
                raise RuntimeError("found an unsigned bit shift.")
            if isinstance(op, AEqualBinaryOp):
                return "=="
            if isinstance(op, ANequalBinaryOp):
                return "!="
            if isinstance(op, ALtBinaryOp):
                return "<"
            if isinstance(op, ALeqBinaryOp):
                return "<="
            if isinstance(op, AGtBinaryOp):
                return ">"
            if isinstance(op, AGeqBinaryOp):
                return ">="
            raise RuntimeError("unknown binary op")
        if isinstance(node, ALogiiCommand):
            op = node.get_logii_op()
            if isinstance(op, AAndLogiiOp):
                return "&&"
            if isinstance(op, AOrLogiiOp):
                return "||"
            if isinstance(op, AInclOrLogiiOp):
                return "|"
            if isinstance(op, AExclOrLogiiOp):
                return "^"
            if isinstance(op, ABitAndLogiiOp):
                return "&"
            raise RuntimeError("unknown logii op")
        if isinstance(node, AStackCommand):
            op = node.get_stack_op()
            if isinstance(op, (ADecispStackOp, ADecibpStackOp)):
                return "--"
            if isinstance(op, (AIncispStackOp, AIncibpStackOp)):
                return "++"
            raise RuntimeError("unknown relative-to-stack unary modifier op")
        raise RuntimeError("unknown node type for get_op")

    @staticmethod
    def is_global_stack_op(node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_incibp_stack_op import AIncibpStackOp  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_decibp_stack_op import ADecibpStackOp  # pyright: ignore[reportMissingImports]
        if not isinstance(node, AStackCommand):
            return False
        op = node.get_stack_op()
        return isinstance(op, (AIncibpStackOp, ADecibpStackOp))

    @staticmethod
    def get_param1_size(node) -> int:
        type_val = NodeUtils.get_type(node)
        if type_val.equals(59) or type_val.equals(58):
            return 3
        return 1

    @staticmethod
    def get_param2_size(node) -> int:
        type_val = NodeUtils.get_type(node)
        if type_val.equals(60) or type_val.equals(58):
            return 3
        return 1

    @staticmethod
    def get_result_size(node) -> int:
        type_val = NodeUtils.get_type(node)
        if type_val.equals(60) or type_val.equals(59) or type_val.equals(58):
            return 3
        return 1

    @staticmethod
    def get_const_value(node):
        from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_int_constant import AIntConstant  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_float_constant import AFloatConstant  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_string_constant import AStringConstant  # pyright: ignore[reportMissingImports]
        if not isinstance(node, AConstCommand):
            return None
        pconst = node.get_constant()
        type_val = NodeUtils.get_type(node)
        if type_val.byte_value() == 3:
            return int(AIntConstant(pconst).get_integer_constant().get_text())
        if type_val.byte_value() == 4:
            return float(AFloatConstant(pconst).get_float_constant().get_text())
        if type_val.byte_value() == 5:
            return AStringConstant(pconst).get_string_literal().get_text()
        if type_val.byte_value() == 6:
            return int(AIntConstant(pconst).get_integer_constant().get_text())
        raise RuntimeError("Invalid const type " + str(type_val))

    @staticmethod
    def get_sub_end(sub) -> int:
        return NodeUtils.get_command_pos(sub.get_return())

    @staticmethod
    def get_action_id(node) -> int:
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        if not isinstance(node, AActionCommand):
            return -1
        return int(node.get_id().get_text())

    @staticmethod
    def get_action_param_count(node) -> int:
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        if not isinstance(node, AActionCommand):
            return 0
        return int(node.get_arg_count().get_text())

    @staticmethod
    def get_action_name(node: Node, actions: ActionsData) -> str:
        return actions.get_name(NodeUtils.get_action_id(node))

    @staticmethod
    def get_action_param_types(node: Node, actions: ActionsData) -> list:
        return actions.get_param_types(NodeUtils.get_action_id(node))

    @staticmethod
    def action_remove_element_count(node: Node, actions: ActionsData) -> int:
        types = NodeUtils.get_action_param_types(node, actions)
        count = NodeUtils.get_action_param_count(node)
        remove = 0
        for i in range(count):
            remove += types[i].type_size()
        return NodeUtils.stack_size_to_pos(remove)

    @staticmethod
    def stack_offset_to_pos(offset) -> int:
        return -int(offset.get_text()) // 4

    @staticmethod
    def stack_size_to_pos(offset) -> int:
        if hasattr(offset, 'get_text'):
            return int(offset.get_text()) // 4
        return offset // 4

    @staticmethod
    def get_command_child(node: Node) -> Node:
        if NodeUtils.is_command_node(node):
            return node
        from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_add_var_cmd import AAddVarCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_jump_cmd import AActionJumpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_const_cmd import AConstCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copydownsp_cmd import ACopydownspCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copytopsp_cmd import ACopytopspCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copydownbp_cmd import ACopydownbpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copytopbp_cmd import ACopytopbpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_cond_jump_cmd import ACondJumpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_cmd import AJumpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_sub_cmd import AJumpSubCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_movesp_cmd import AMovespCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_cmd import ALogiiCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unary_cmd import AUnaryCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_cmd import ABinaryCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_cmd import ADestructCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_bp_cmd import ABpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_cmd import AActionCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_stack_op_cmd import AStackOpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return_cmd import AReturnCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_cmd import AStoreStateCmd  # pyright: ignore[reportMissingImports]
        if isinstance(node, ASubroutine):
            return NodeUtils.get_command_child(node.get_command_block())
        if isinstance(node, ACommandBlock):
            cmds = node.get_cmd()
            if len(cmds) > 0:
                return NodeUtils.get_command_child(cmds[0])
        if isinstance(node, AAddVarCmd):
            return NodeUtils.get_command_child(node.get_rsadd_command())
        if isinstance(node, AActionJumpCmd):
            return NodeUtils.get_command_child(node.get_store_state_command())
        if isinstance(node, AConstCmd):
            return NodeUtils.get_command_child(node.get_const_command())
        if isinstance(node, ACopydownspCmd):
            return NodeUtils.get_command_child(node.get_copy_down_sp_command())
        if isinstance(node, ACopytopspCmd):
            return NodeUtils.get_command_child(node.get_copy_top_sp_command())
        if isinstance(node, ACopydownbpCmd):
            return NodeUtils.get_command_child(node.get_copy_down_bp_command())
        if isinstance(node, ACopytopbpCmd):
            return NodeUtils.get_command_child(node.get_copy_top_bp_command())
        if isinstance(node, ACondJumpCmd):
            return NodeUtils.get_command_child(node.get_conditional_jump_command())
        if isinstance(node, AJumpCmd):
            return NodeUtils.get_command_child(node.get_jump_command())
        if isinstance(node, AJumpSubCmd):
            return NodeUtils.get_command_child(node.get_jump_to_subroutine())
        if isinstance(node, AMovespCmd):
            return NodeUtils.get_command_child(node.get_move_sp_command())
        if isinstance(node, ALogiiCmd):
            return NodeUtils.get_command_child(node.get_logii_command())
        if isinstance(node, AUnaryCmd):
            return NodeUtils.get_command_child(node.get_unary_command())
        if isinstance(node, ABinaryCmd):
            return NodeUtils.get_command_child(node.get_binary_command())
        if isinstance(node, ADestructCmd):
            return NodeUtils.get_command_child(node.get_destruct_command())
        if isinstance(node, ABpCmd):
            return NodeUtils.get_command_child(node.get_bp_command())
        if isinstance(node, AActionCmd):
            return NodeUtils.get_command_child(node.get_action_command())
        if isinstance(node, AStackOpCmd):
            return NodeUtils.get_command_child(node.get_stack_command())
        if isinstance(node, AReturnCmd):
            return NodeUtils.get_command_child(node.get_return())
        if isinstance(node, AStoreStateCmd):
            return NodeUtils.get_command_child(node.get_store_state_command())
        raise RuntimeError("unexpected node type " + str(node))

    @staticmethod
    def get_previous_command(node: Node, nodedata: NodeAnalysisData) -> Node | None:
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
        if isinstance(node, AReturn):
            ablock: ACommandBlock = node.parent().get_command_block()
            cmds = ablock.get_cmd()
            if len(cmds) > 0:
                return NodeUtils.get_command_child(cmds[-1])
        up = node.parent()
        while up is not None and not isinstance(up, ACommandBlock):
            up = up.parent()
        if up is None:
            return None
        search_pos = nodedata.get_pos(node)
        cmds = up.get_cmd()
        for i, cmd in enumerate(cmds):
            if nodedata.get_pos(cmd) == search_pos:
                if i > 0:
                    return NodeUtils.get_command_child(cmds[i - 1])
                return None
        return None

    @staticmethod
    def get_next_command(node: Node, nodedata: NodeAnalysisData) -> Node | None:
        from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
        up = node.parent()
        while up is not None and not isinstance(up, ACommandBlock):
            up = up.parent()
        if up is None:
            return None
        search_pos = nodedata.get_pos(node)
        cmds = up.get_cmd()
        for i, cmd in enumerate(cmds):
            if nodedata.get_pos(cmd) == search_pos:
                if i + 1 < len(cmds):
                    return NodeUtils.get_command_child(cmds[i + 1])
                return None
        return None

    @staticmethod
    def is_return(node: Node) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.a_return_cmd import AReturnCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        return isinstance(node, (AReturnCmd, AReturn))

    @staticmethod
    def get_type(node: Node) -> Type:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_down_bp_command import ACopyDownBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_copy_top_bp_command import ACopyTopBpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_logii_command import ALogiiCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_unary_command import AUnaryCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_stack_command import AStackCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_destruct_command import ADestructCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_bp_command import ABpCommand  # pyright: ignore[reportMissingImports]
        if isinstance(node, AConditionalJumpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AJumpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AJumpToSubroutine):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AReturn):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ACopyDownSpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ACopyTopSpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ACopyDownBpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ACopyTopBpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AMoveSpCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ARsaddCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AConstCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AActionCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ALogiiCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ABinaryCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AUnaryCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, AStackCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ADestructCommand):
            return Type(int(node.get_type().get_text()))
        if isinstance(node, ABpCommand):
            return Type(int(node.get_type().get_text()))
        raise RuntimeError("No type for this node type: " + str(node))

    @staticmethod
    def get_return_type(node: Node, actions: ActionsData = None) -> Type:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_binary_command import ABinaryCommand  # pyright: ignore[reportMissingImports]
        if isinstance(node, AActionCommand):
            return actions.get_return_type(NodeUtils.get_action_id(node))
        if isinstance(node, ABinaryCommand):
            nodetype = int(node.get_type().get_text())
            if nodetype in (60, 59, 58):
                type_val = -16
            elif nodetype == 32:
                type_val = 3
            elif nodetype in (37, 38, 33):
                type_val = 4
            elif nodetype == 35:
                type_val = 5
            else:
                raise RuntimeError("Unexpected type " + str(nodetype))
            return Type(type_val)
        raise RuntimeError("No return type for this node type: " + str(node))

    @staticmethod
    def is_conditional_program(ast) -> bool:
        from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
        if not isinstance(ast, Start):
            return False
        program = ast.get_p_program()
        return program.get_conditional() is not None

