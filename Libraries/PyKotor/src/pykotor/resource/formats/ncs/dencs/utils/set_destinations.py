from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_conditional_jump_command import AConditionalJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class SetDestinations(PrunedDepthFirstAdapter):
    def __init__(self, ast: Node, nodedata: NodeAnalysisData, subdata: SubroutineAnalysisData):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.nodedata: NodeAnalysisData = nodedata
        self.current_pos: int = 0
        self.ast: Node = ast
        self.subdata: SubroutineAnalysisData = subdata
        self.actionarg: int = 0
        self.origins: dict[Node, list[Node]] = {}
        self.destination: Node | None = None

    def done(self):
        self.nodedata = None
        self.subdata = None
        self.destination = None
        self.ast = None
        self.origins = None

    def get_origins(self) -> dict[Node, list[Node]]:
        return self.origins

    def out_a_conditional_jump_command(self, node: AConditionalJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, True)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        self.add_destination(node, self.destination)

    def out_a_jump_command(self, node: AJumpCommand):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, True)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        if pos < self.nodedata.get_pos(node):
            dest = NodeUtils.get_command_child(self.destination)
            self.nodedata.add_origin(dest, node)
        self.add_destination(node, self.destination)

    def out_a_jump_to_subroutine(self, node: AJumpToSubroutine):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        pos = NodeUtils.get_jump_destination_pos(node)
        self.look_for_pos(pos, False)
        if self.destination is None:
            raise RuntimeError("wasn't able to find dest for " + str(node) + " at pos " + str(pos))
        self.nodedata.set_destination(node, self.destination)
        self.add_destination(node, self.destination)

    def add_destination(self, origin: Node, destination: Node):
        if destination not in self.origins:
            self.origins[destination] = []
        self.origins[destination].append(origin)

    def get_pos(self, node: Node) -> int:
        return self.nodedata.get_pos(node)

    def look_for_pos(self, pos: int, needcommand: bool):
        self.destination = None
        
        class LookForPosAdapter(PrunedDepthFirstAdapter):
            def __init__(self, outer, pos, needcommand):
                from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
                super().__init__()
                self.outer = outer
                self.pos = pos
                self.needcommand = needcommand

            def default_in(self, node: Node):
                from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
                if self.outer.get_pos(node) == self.pos and self.outer.destination is None and (not self.needcommand or NodeUtils.is_command_node(node)):
                    self.outer.destination = node

            def case_a_program(self, node: AProgram):
                self.in_a_program(node)
                if node.get_return() is not None:
                    node.get_return().apply(self)
                temp = list(node.get_subroutine())
                cur = len(temp) // 2
                min_idx = 0
                max_idx = len(temp) - 1
                done = self.outer.destination is not None or cur >= len(temp)
                while not done:
                    sub = temp[cur]
                    if self.outer.get_pos(sub) > self.pos:
                        max_idx = cur
                        cur = (min_idx + cur) // 2
                    elif self.outer.get_pos(sub) == self.pos:
                        sub.apply(self)
                        done = True
                    elif cur >= max_idx - 1:
                        sub.apply(self)
                        cur += 1
                    else:
                        min_idx = cur
                        cur = (cur + max_idx) // 2
                    done = done or self.outer.destination is not None or cur > max_idx
                self.out_a_program(node)

            def case_a_command_block(self, node: ACommandBlock):
                self.in_a_command_block(node)
                temp = list(node.get_cmd())
                cur = len(temp) // 2
                min_idx = 0
                max_idx = len(temp) - 1
                done = self.outer.destination is not None or cur >= len(temp)
                while not done:
                    cmd = temp[cur]
                    if self.outer.get_pos(cmd) > self.pos:
                        max_idx = cur
                        cur = (min_idx + cur) // 2
                    elif self.outer.get_pos(cmd) == self.pos:
                        cmd.apply(self)
                        done = True
                    elif cur >= max_idx - 1:
                        cmd.apply(self)
                        cur += 1
                    else:
                        min_idx = cur
                        cur = (cur + max_idx) // 2
                    done = done or self.outer.destination is not None or cur > max_idx

        adapter = LookForPosAdapter(self, pos, needcommand)
        self.ast.apply(adapter)

