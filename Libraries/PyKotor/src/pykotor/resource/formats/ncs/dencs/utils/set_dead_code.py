from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class SetDeadCode(PrunedDepthFirstAdapter):
    STATE_NORMAL = 0
    STATE_JZ1_CP = 1
    STATE_JZ2_JZ = 2
    STATE_JZ3_CP2 = 3

    def __init__(self, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData, origins: dict[Node, list[Node]]):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.origins: dict[Node, list[Node]] = origins
        self.subdata: SubroutineAnalysisData = subdata
        self.actionarg: int = 0
        self.deadstate: int = 0
        self.state: int = 0
        self.deadorigins: dict[Node, list[Node]] = {}

    def done(self):
        self.nodedata = None
        self.subdata = None
        self.origins = None
        self.deadorigins = None

    def default_in(self, node: Node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if self.actionarg > 0 and node in self.origins:
            self.actionarg -= 1
        if node in self.origins:
            self.deadstate = 0
        elif node in self.deadorigins:
            self.deadstate = 3
        if NodeUtils.is_command_node(node):
            self.nodedata.set_code_state(node, self.deadstate)

    def default_out(self, node: Node):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if NodeUtils.is_command_node(node):
            self.state = 0

    def out_a_conditional_jump_command(self, node: AConditionalJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if self.deadstate == 1:
            self.remove_destination(node, self.nodedata.get_destination(node))
        elif self.deadstate == 3:
            self.transfer_destination(node, self.nodedata.get_destination(node))
        if NodeUtils.is_jz(node):
            if self.state == 1:
                self.state += 1
                return
            if self.state == 3:
                self.nodedata.log_or_code(node, True)
        self.state = 0

    def out_a_copy_top_sp_command(self, node: ACopyTopSpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        if self.state == 0 or self.state == 2:
            copy = NodeUtils.stack_size_to_pos(node.get_size())
            loc = NodeUtils.stack_offset_to_pos(node.get_offset())
            if copy == 1 and loc == 1:
                self.state += 1
            else:
                self.state = 0
        else:
            self.state = 0

    def out_a_jump_command(self, node: AJumpCommand):
        if self.deadstate == 1:
            self.remove_destination(node, self.nodedata.get_destination(node))
        elif self.deadstate == 3:
            self.transfer_destination(node, self.nodedata.get_destination(node))
        if self.actionarg == 0:
            self.deadstate = 3
        self.default_out(node)

    def out_a_store_state_command(self, node: AStoreStateCommand):
        self.actionarg += 1
        self.default_out(node)

    def is_jump_to_return(self, node: AJumpCommand) -> bool:
        dest = self.nodedata.get_destination(node)
        return isinstance(dest, AReturn)

    def remove_destination(self, origin: Node, destination: Node):
        self.remove_destination(origin, destination, self.origins)

    def remove_destination(self, origin: Node, destination: Node, hash_dict: dict[Node, list[Node]]):
        if destination not in hash_dict:
            return
        originlist = hash_dict[destination]
        if origin in originlist:
            originlist.remove(origin)
        if len(originlist) == 0:
            del hash_dict[destination]

    def transfer_destination(self, origin: Node, destination: Node):
        self.remove_destination(origin, destination, self.origins)
        self.add_destination(origin, destination, self.deadorigins)

    def add_destination(self, origin: Node, destination: Node, hash_dict: dict[Node, list[Node]]):
        if destination not in hash_dict:
            hash_dict[destination] = []
        hash_dict[destination].append(origin)

