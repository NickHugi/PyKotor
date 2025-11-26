from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_action_jump_cmd import AActionJumpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_add_var_cmd import AAddVarCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_const_cmd import AConstCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copydownsp_cmd import ACopydownspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copytopsp_cmd import ACopytopspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copydownbp_cmd import ACopydownbpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copytopbp_cmd import ACopytopbpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_movesp_cmd import AMovespCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_logii_cmd import ALogiiCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_unary_cmd import AUnaryCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_binary_cmd import ABinaryCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_destruct_cmd import ADestructCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_bp_cmd import ABpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_action_cmd import AActionCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_stack_op_cmd import AStackOpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]


class FlattenSub(PrunedDepthFirstAdapter):
    def __init__(self, sub: ASubroutine, nodedata: NodeAnalysisData):
        from pykotor.resource.formats.ncs.dencs.analysis.pruned_depth_first_adapter import PrunedDepthFirstAdapter  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.set_sub(sub)
        self.actionjumpfound: bool = False
        self.nodedata: NodeAnalysisData = nodedata

    def done(self):
        self.sub = None
        self.commands = None
        self.nodedata = None

    def set_sub(self, sub: ASubroutine):
        self.sub: ASubroutine = sub

    def case_a_command_block(self, node: ACommandBlock):
        self.commands = node.get_cmd()
        self.i = 0
        while self.i < len(self.commands):
            self.commands[self.i].apply(self)
            if self.actionjumpfound:
                self.actionjumpfound = False
            else:
                self.i += 1

    def case_a_action_jump_cmd(self, node: AActionJumpCmd):
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_command import AStoreStateCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_store_state_cmd import AStoreStateCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_jump_cmd import AJumpCmd  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_return_cmd import AReturnCmd  # pyright: ignore[reportMissingImports]
        sscommand: AStoreStateCommand = node.get_store_state_command()
        jmpcommand: AJumpCommand = node.get_jump_command()
        cmdblock: ACommandBlock = node.get_command_block()
        rtn: AReturn = node.get_return()
        sscmd = AStoreStateCmd(sscommand)
        jmpcmd = AJumpCmd(jmpcommand)
        rtncmd = AReturnCmd(rtn)
        self.nodedata.set_pos(sscmd, self.nodedata.get_pos(sscommand))
        self.nodedata.set_pos(jmpcmd, self.nodedata.get_pos(jmpcommand))
        self.nodedata.set_pos(rtncmd, self.nodedata.get_pos(rtn))
        j = self.i
        self.commands[j] = sscmd
        j += 1
        self.commands.insert(j, jmpcmd)
        j += 1
        subcmds = cmdblock.get_cmd()
        while len(subcmds) > 0:
            self.commands.insert(j, subcmds.pop(0))
            j += 1
        self.commands.insert(j, rtncmd)
        self.actionjumpfound = True

    def case_a_add_var_cmd(self, node: AAddVarCmd):
        pass

    def case_a_const_cmd(self, node: AConstCmd):
        pass

    def case_a_copydownsp_cmd(self, node: ACopydownspCmd):
        pass

    def case_a_copytopsp_cmd(self, node: ACopytopspCmd):
        pass

    def case_a_copydownbp_cmd(self, node: ACopydownbpCmd):
        pass

    def case_a_copytopbp_cmd(self, node: ACopytopbpCmd):
        pass

    def case_a_movesp_cmd(self, node: AMovespCmd):
        pass

    def case_a_logii_cmd(self, node: ALogiiCmd):
        pass

    def case_a_unary_cmd(self, node: AUnaryCmd):
        pass

    def case_a_binary_cmd(self, node: ABinaryCmd):
        pass

    def case_a_destruct_cmd(self, node: ADestructCmd):
        pass

    def case_a_bp_cmd(self, node: ABpCmd):
        pass

    def case_a_action_cmd(self, node: AActionCmd):
        pass

    def case_a_stack_op_cmd(self, node: AStackOpCmd):
        pass

