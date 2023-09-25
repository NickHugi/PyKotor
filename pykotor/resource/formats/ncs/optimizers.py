from copy import copy

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType, NCSOptimizer


class RemoveNopOptimizer(NCSOptimizer):
    """NCS Compiler uses NOP instructions as stubs to simplify the compilation process however as their name suggests
    they do not perform any actual function. This optimizer removes all occurrences of NOP instructions from the
    compiled script.
    """

    def optimize(self, ncs: NCS) -> None:
        nops = [inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.NOP]

        # Process instructions which jump to a NOP and set them to jump to the proceeding instruction instead
        for nop in nops:
            nop_index = ncs.instructions.index(nop)
            for link in ncs.links_to(nop):
                link.jump = ncs.instructions[nop_index + 1]

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
        raise NotImplementedError


class RemoveJMPToAdjacentOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError


class RemoveUnusedBlocksOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        # Find list of unreachable instructions
        reachable = set()
        checking = [0]
        while checking:
            check = checking.pop(0)
            if check > len(ncs.instructions):
                continue

            instruction = ncs.instructions[check]
            if instruction in reachable:
                continue
            reachable.add(instruction)

            if instruction.ins_type in [
                NCSInstructionType.JZ,
                NCSInstructionType.JNZ,
                NCSInstructionType.JSR,
            ]:
                checking.append(ncs.instructions.index(instruction.jump))
                checking.append(check + 1)
            elif instruction.ins_type in [NCSInstructionType.JMP]:
                checking.append(ncs.instructions.index(instruction.jump))
            elif instruction.ins_type in [NCSInstructionType.RETN]:
                ...
            else:
                checking.append(check + 1)

        unreachable = [instruction for instruction in ncs.instructions if instruction not in reachable]
        for instruction in unreachable:
            # We do not have to worry about fixing any instructions that JMP since the target instructions here should
            # be detached for the actual (reachable) script.
            ncs.instructions.remove(instruction)
            self.instructions_cleared += 1


class RemoveUnusedGlobalsInStackOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> None:
        raise NotImplementedError
