from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]


class AnalysisAdapter:
    def __init__(self):
        self._in: dict[Node, Any] = {}
        self._out: dict[Node, Any] = {}

    def get_in(self, node: Node) -> Any:
        return self._in.get(node)

    def set_in(self, node: Node, value: Any):
        if value is not None:
            self._in[node] = value
        elif node in self._in:
            del self._in[node]

    def get_out(self, node: Node) -> Any:
        return self._out.get(node)

    def set_out(self, node: Node, value: Any):
        if value is not None:
            self._out[node] = value
        elif node in self._out:
            del self._out[node]

    def default_in(self, node: Node):
        pass

    def default_out(self, node: Node):
        pass

    def default_case(self, node: Node):
        pass

    def case_node(self, node: Node):
        self.default_case(node)

    def case_a_program(self, node):
        self.default_case(node)

    def case_a_subroutine(self, node):
        self.default_case(node)

    def case_a_command_block(self, node):
        self.default_case(node)

    def case_a_const_cmd(self, node):
        self.default_case(node)

    def case_a_jump_cmd(self, node):
        self.default_case(node)

    def case_a_jump_sub_cmd(self, node):
        self.default_case(node)

    def case_a_return_cmd(self, node):
        self.default_case(node)

    def case_a_const_command(self, node):
        self.default_case(node)

    def case_a_jump_command(self, node):
        self.default_case(node)

    def case_a_jump_to_subroutine(self, node):
        self.default_case(node)

    def case_a_return(self, node):
        self.default_case(node)

    def case_a_int_constant(self, node):
        self.default_case(node)

    def case_a_float_constant(self, node):
        self.default_case(node)

    def case_a_string_constant(self, node):
        self.default_case(node)

    def case_t_const(self, node):
        self.default_case(node)

    def case_t_semi(self, node):
        self.default_case(node)

    def case_t_jmp(self, node):
        self.default_case(node)

    def case_t_jsr(self, node):
        self.default_case(node)

    def case_t_retn(self, node):
        self.default_case(node)

    def case_t_integer_constant(self, node):
        self.default_case(node)

    def case_t_float_constant(self, node):
        self.default_case(node)

    def case_t_string_literal(self, node):
        self.default_case(node)

    def case_t_action(self, node):
        self.default_case(node)

    def case_t_cpdownsp(self, node):
        self.default_case(node)

    def case_t_cptopsp(self, node):
        self.default_case(node)

    def case_t_movsp(self, node):
        self.default_case(node)

    def case_t_rsadd(self, node):
        self.default_case(node)

    def case_a_action_cmd(self, node):
        self.default_case(node)

    def case_a_action_command(self, node):
        self.default_case(node)

    def case_a_copydownsp_cmd(self, node):
        self.default_case(node)

    def case_a_copytopsp_cmd(self, node):
        self.default_case(node)

    def case_a_copy_down_sp_command(self, node):
        self.default_case(node)

    def case_a_copy_top_sp_command(self, node):
        self.default_case(node)

    def case_a_movesp_cmd(self, node):
        self.default_case(node)

    def case_a_move_sp_command(self, node):
        self.default_case(node)

    def case_a_rsadd_cmd(self, node):
        self.default_case(node)

    def case_a_rsadd_command(self, node):
        self.default_case(node)

