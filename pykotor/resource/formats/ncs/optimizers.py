from copy import copy

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.ncs_data import NCSOptimizer, NCSInstructionType


class RemoveNopOptimizer(NCSOptimizer):
    """
    NCS Compiler uses NOP instructions as stubs to simplify the compilation process however as their name suggests
    they do not perform any actual function. This optimizer removes all occurrences of NOP instructions from the
    compiled script.
    """

    def optimize(self, ncs: NCS) -> None:
        nops = [inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.NOP]

        # Process instructions which jump to a NOP and set them to jump to the proceeding instruction instead
        for nop in nops:
            nop_index = ncs.instructions.index(nop)
            for link in ncs.links_to(nop):
                link.jump = ncs.instructions[nop_index+1]

        # It is now safe to remove all NOP instructions
        ncs.instructions = [inst for inst in ncs.instructions if inst.ins_type != NCSInstructionType.NOP]


class RemoveMoveSPEqualsZeroOptimizer(NCSOptimizer):
    def __init__(self):
        super().__init__()

    def optimize(self, ncs: NCS) -> None:
        movsp0 = [inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.MOVSP and inst.args[0] == 0]

        # Process instructions which jump to a MOVSP=0 and set them to jump to the proceeding instruction instead
        for op in movsp0:
            nop_index = ncs.instructions.index(op)
            for link in ncs.links_to(op):
                link.jump = ncs.instructions[nop_index + 1]

        # It is now safe to remove all MOVSP=0 instructions
        for inst in copy(ncs.instructions):
            if inst.ins_type == NCSInstructionType.MOVSP and inst.args[0] == 0:
                ncs.instructions.remove(inst)
                self.instructions_cleared += 1


class MergeAdjacentMoveSPOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError()


class RemoveJMPToAdjacentOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError()


class RemoveUnusedBlocksOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError()


class RemoveUnusedGlobalsInStackOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError()
