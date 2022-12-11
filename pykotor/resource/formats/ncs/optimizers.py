from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.ncs_data import NCSOptimizer, NCSInstructionType


class RemoveNopOptimizer(NCSOptimizer):
    """
    NCS Compiler uses NOP instructions as stubs to simplify the compilation process however as their name suggests
    they do not perform any actual function. This optimizer removes all occureses of NOP instructions from the
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
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError()


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
