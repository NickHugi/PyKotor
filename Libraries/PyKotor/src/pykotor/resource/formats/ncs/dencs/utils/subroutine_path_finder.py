from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class SubroutinePathFinder(PrunedDepthFirstAdapter):
    def __init__(self, state: SubroutineState, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData, pass_num: int):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.subdata: SubroutineAnalysisData = subdata
        self.state: SubroutineState = state
        self.pathfailed: bool = False
        self.forcejump: bool = False
        self.limitretries: bool = pass_num < 3
        if pass_num == 0:
            self.maxretry: int = 10
        elif pass_num == 1:
            self.maxretry: int = 15
        elif pass_num == 2:
            self.maxretry: int = 25
        else:
            self.maxretry: int = 9999
        self.retry: int = 0
        self.destinationcommands: dict[int, int] = {}

    def done(self):
        self.nodedata = None
        self.subdata = None
        self.state = None
        self.destinationcommands = None

    def in_a_subroutine(self, node: ASubroutine):
        self.state.start_prototyping()

    def case_a_command_block(self, node: ACommandBlock):
        self.in_a_command_block(node)
        commands = node.get_cmd()
        self.setup_destination_commands(commands, node)
        i = 0
        while i < len(commands):
            if self.forcejump:
                next_pos = self.state.get_current_destination()
                i = self.destinationcommands.get(next_pos, i)
                self.forcejump = False
            elif self.pathfailed:
                next_pos = self.state.switch_decision()
                if next_pos == -1 or (self.limitretries and self.retry > self.maxretry):
                    self.state.stop_prototyping(False)
                    return
                i = self.destinationcommands.get(next_pos, i)
                self.pathfailed = False
                self.retry += 1
            if i < len(commands):
                commands[i].apply(self)
                i += 1
        self.out_a_command_block(node)

    def out_a_conditional_jump_command(self, node: AConditionalJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        NodeUtils.get_next_command(node, self.nodedata)
        if not self.nodedata.log_or_code(node):
            self.state.add_decision(node, NodeUtils.get_jump_destination_pos(node))

    def out_a_jump_command(self, node: AJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if NodeUtils.get_jump_destination_pos(node) < self.nodedata.get_pos(node):
            self.pathfailed = True
        else:
            self.state.add_jump(node, NodeUtils.get_jump_destination_pos(node))
            self.forcejump = True

    def out_a_jump_to_subroutine(self, node: AJumpToSubroutine):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if not self.subdata.is_prototyped(NodeUtils.get_jump_destination_pos(node), True):
            self.pathfailed = True

    def case_a_add_var_cmd(self, node):
        pass

    def case_a_const_cmd(self, node):
        pass

    def case_a_copydownsp_cmd(self, node):
        pass

    def case_a_copytopsp_cmd(self, node):
        pass

    def case_a_copydownbp_cmd(self, node):
        pass

    def case_a_copytopbp_cmd(self, node):
        pass

    def case_a_movesp_cmd(self, node):
        pass

    def case_a_logii_cmd(self, node):
        pass

    def case_a_unary_cmd(self, node):
        pass

    def case_a_binary_cmd(self, node):
        pass

    def case_a_destruct_cmd(self, node):
        pass

    def case_a_bp_cmd(self, node):
        pass

    def case_a_action_cmd(self, node):
        pass

    def case_a_stack_op_cmd(self, node):
        pass

    def setup_destination_commands(self, commands: list, ast: Node):
        from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        
        class SetupAdapter(PrunedDepthFirstAdapter):
            def __init__(self, outer, commands):
                from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
                super().__init__()
                self.outer = outer
                self.commands = commands

            def out_a_conditional_jump_command(self, node: AConditionalJumpCommand):
                pos = NodeUtils.get_jump_destination_pos(node)
                self.outer.destinationcommands[pos] = self.outer.get_command_index_by_pos(pos, self.commands)

            def out_a_jump_command(self, node: AJumpCommand):
                pos = NodeUtils.get_jump_destination_pos(node)
                self.outer.destinationcommands[pos] = self.outer.get_command_index_by_pos(pos, self.commands)

            def case_a_add_var_cmd(self, node):
                pass

            def case_a_const_cmd(self, node):
                pass

            def case_a_copydownsp_cmd(self, node):
                pass

            def case_a_copytopsp_cmd(self, node):
                pass

            def case_a_copydownbp_cmd(self, node):
                pass

            def case_a_copytopbp_cmd(self, node):
                pass

            def case_a_movesp_cmd(self, node):
                pass

            def case_a_logii_cmd(self, node):
                pass

            def case_a_unary_cmd(self, node):
                pass

            def case_a_binary_cmd(self, node):
                pass

            def case_a_destruct_cmd(self, node):
                pass

            def case_a_bp_cmd(self, node):
                pass

            def case_a_action_cmd(self, node):
                pass

            def case_a_stack_op_cmd(self, node):
                pass

        adapter = SetupAdapter(self, commands)
        ast.apply(adapter)

    def get_command_index_by_pos(self, pos: int, commands: list) -> int:
        if len(commands) == 0:
            raise RuntimeError("Unable to locate a command with position " + str(pos))
        node = commands[0]
        i = 1
        while i < len(commands) and self.nodedata.get_pos(node) < pos:
            node = commands[i]
            if self.nodedata.get_pos(node) == pos:
                break
            i += 1
        if self.nodedata.get_pos(node) > pos:
            raise RuntimeError("Unable to locate a command with position " + str(pos))
        return i

