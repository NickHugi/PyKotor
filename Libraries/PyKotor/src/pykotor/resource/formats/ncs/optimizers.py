from __future__ import annotations

import logging

from typing import TYPE_CHECKING, NoReturn

from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType, NCSOptimizer

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.ncs_data import NCS, NCSInstruction


logger = logging.getLogger(__name__)


class RemoveNopOptimizer(NCSOptimizer):
    """Removes NOP (no-operation) instructions from compiled NCS bytecode.
    
    NCS Compiler uses NOP instructions as stubs to simplify the compilation process
    however as their name suggests they do not perform any actual function. This optimizer
    removes all occurrences of NOP instructions from the compiled script, updating jump
    targets to skip over removed NOPs.
    
    References:
    ----------
        vendor/xoreos-tools/src/nwscript/decompiler.cpp (NCS optimization patterns)
        Standard compiler optimization techniques (dead code elimination)
        Note: NOP removal is a common bytecode optimization
    """  # noqa: D205

    def optimize(self, ncs: NCS):
        """Optimizes a neural circuit specification by removing NOP instructions.

        Args:
        ----
            ncs: NCS - The neural circuit specification to optimize

        Processing Logic:
        ----------------
            - Finds all NOP instructions in the NCS
            - For each NOP, finds all links jumping to it and updates them to jump to the next instruction instead
            - Removes all NOP instructions from the NCS instruction list.
        """
        def find_index(target: NCSInstruction) -> int:
            for idx, instruction in enumerate(ncs.instructions):
                if instruction is target:
                    return idx
            msg = f"NOP not present by identity lookup. nop_id={id(target)}"
            raise ValueError(msg)

        nops: list[NCSInstruction] = [inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.NOP]

        if not nops:
            return

        removable_ids: set[int] = set()

        # Process instructions which jump to a NOP and set them to jump to the proceeding non-NOP instruction instead.
        for nop in nops:
            try:
                nop_index: int = find_index(nop)
            except ValueError:
                logger.warning("Skipping NOP removal; lookup failed. nop_id=%s", id(nop), exc_info=True)
                continue

            inbound_links = ncs.links_to(nop)
            replacement: NCSInstruction | None = None

            for candidate in ncs.instructions[nop_index + 1 :]:
                if candidate.ins_type != NCSInstructionType.NOP:
                    replacement = candidate
                    break

            if inbound_links and replacement is None:
                # We cannot safely retarget inbound jumps, so keep this NOP.
                continue

            for link in inbound_links:
                link.jump = replacement

            removable_ids.add(id(nop))

        if not removable_ids:
            return

        ncs.instructions = [inst for inst in ncs.instructions if id(inst) not in removable_ids]
        self.instructions_cleared += len(removable_ids)


class RemoveMoveSPEqualsZeroOptimizer(NCSOptimizer):
    def __init__(self):
        super().__init__()

    def optimize(self, ncs: NCS):
        movsp0: list[NCSInstruction] = [inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.MOVSP and inst.args[0] == 0]

        # Process instructions which jump to a MOVSP=0 and set them to jump to the proceeding instruction instead
        for op in movsp0:
            nop_index: int = ncs.instructions.index(op)
            for link in ncs.links_to(op):
                link.jump = ncs.instructions[nop_index + 1]

        # It is now safe to remove all MOVSP=0 instructions
        for inst in ncs.instructions.copy():
            if inst.ins_type == NCSInstructionType.MOVSP and inst.args[0] == 0:
                ncs.instructions.remove(inst)
                self.instructions_cleared += 1


class MergeAdjacentMoveSPOptimizer(NCSOptimizer):
    """Merges consecutive MOVSP instructions into a single instruction.

    Multiple adjacent stack pointer movements can be combined into one,
    reducing bytecode size and improving execution efficiency.
    """

    def optimize(self, ncs: NCS):
        i = 0
        while i < len(ncs.instructions) - 1:
            instruction = ncs.instructions[i]

            if instruction.ins_type != NCSInstructionType.MOVSP:
                i += 1
                continue

            # Check if next instruction is also MOVSP and nothing jumps to it
            next_inst = ncs.instructions[i + 1]
            if next_inst.ins_type == NCSInstructionType.MOVSP and not ncs.links_to(next_inst):
                # Merge: add the offsets together
                combined_offset = instruction.args[0] + next_inst.args[0]
                instruction.args[0] = combined_offset

                # Remove the second MOVSP
                ncs.instructions.remove(next_inst)
                self.instructions_cleared += 1

                # Don't increment i, check if we can merge more
                continue

            i += 1


class RemoveJMPToAdjacentOptimizer(NCSOptimizer):
    """Removes JMP instructions that jump to the immediately following instruction.

    Such jumps are redundant as execution would naturally flow to the next
    instruction anyway.
    """

    def optimize(self, ncs: NCS):
        removals = []

        for i, instruction in enumerate(ncs.instructions[:-1]):  # Skip last instruction
            if instruction.ins_type != NCSInstructionType.JMP:
                continue

            if instruction.jump is None:
                continue

            # Check if this JMP targets the very next instruction
            next_instruction = ncs.instructions[i + 1]
            if instruction.jump is next_instruction:
                # This JMP is redundant
                removals.append(instruction)

        # Remove all redundant JMPs
        for instruction in removals:
            ncs.instructions.remove(instruction)
            self.instructions_cleared += 1


class RemoveUnusedBlocksOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS):
        # Find list of unreachable instructions
        reachable = set()
        checking: list[int] = [0]
        while checking:
            check: int = checking.pop(0)
            if check > len(ncs.instructions):
                continue

            instruction: NCSInstruction = ncs.instructions[check]
            if instruction in reachable:
                continue
            reachable.add(instruction)

            if instruction.ins_type in {
                NCSInstructionType.JZ,
                NCSInstructionType.JNZ,
                NCSInstructionType.JSR,
            }:
                assert instruction.jump is not None, f"{instruction} has a NoneType jump."
                checking.extend((ncs.instructions.index(instruction.jump), check + 1))
            elif instruction.ins_type == NCSInstructionType.JMP:
                assert instruction.jump is not None, f"{instruction} has a NoneType jump."
                checking.append(ncs.instructions.index(instruction.jump))
            elif instruction.ins_type == NCSInstructionType.RETN:
                ...
            else:
                checking.append(check + 1)

        unreachable: list[NCSInstruction] = [instruction for instruction in ncs.instructions if instruction not in reachable]
        for instruction in unreachable:
            # We do not have to worry about fixing any instructions that JMP since the target instructions here should
            # be detached for the actual (reachable) script.
            ncs.instructions.remove(instruction)
            self.instructions_cleared += 1


class RemoveUnusedGlobalsInStackOptimizer(NCSOptimizer):
    def optimize(self, ncs: NCS) -> NoReturn:
        raise NotImplementedError
