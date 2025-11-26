from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.ncs_data import NCS, NCSInstruction, NCSInstructionType  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]


def convert_ncs_to_ast(ncs: NCS) -> AProgram:
    """Convert NCSInstruction[] to DeNCS AST format.

    This replaces the Decoder -> Lexer -> Parser chain by directly
    converting NCSInstruction objects to AST nodes.
    """
    from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    program = AProgram()

    instructions = ncs.instructions
    if not instructions:
        return program

    # Find subroutines (JSR targets)
    subroutine_starts = set()
    for i, inst in enumerate(instructions):
        if inst.ins_type == NCSInstructionType.JSR and inst.jump is not None:
            try:
                jump_idx = ncs.get_instruction_index(inst.jump)
                if jump_idx >= 0:
                    subroutine_starts.add(jump_idx)
            except (ValueError, AttributeError):
                pass

    # The main program starts at instruction 0
    # Create main subroutine (all code until first JSR target or end)
    main_end = len(instructions)
    if subroutine_starts:
        main_end = min(subroutine_starts)

    main_sub = _convert_instruction_range_to_subroutine(instructions, 0, main_end, 0)
    if main_sub:
        program.add_subroutine(main_sub)

    # Convert each subroutine
    for sub_start in sorted(subroutine_starts):
        # Find end of this subroutine (next subroutine or RETN)
        sub_end = len(instructions)
        for i in range(sub_start + 1, len(instructions)):
            if i in subroutine_starts:
                sub_end = i
                break
            if instructions[i].ins_type == NCSInstructionType.RETN:
                sub_end = i + 1
                break

        sub = _convert_instruction_range_to_subroutine(instructions, sub_start, sub_end, len(program.get_subroutine()))
        if sub:
            program.add_subroutine(sub)

    return program


def _convert_instruction_range_to_subroutine(
    instructions: list[NCSInstruction],
    start_idx: int,
    end_idx: int,
    sub_id: int
):
    """Convert a range of instructions to an ASubroutine."""
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_command_block import ACommandBlock  # pyright: ignore[reportMissingImports]

    if start_idx >= end_idx or start_idx >= len(instructions):
        return None

    sub = ASubroutine()
    sub.set_id(sub_id)

    cmd_block = ACommandBlock()

    for i in range(start_idx, min(end_idx, len(instructions))):
        inst = instructions[i]
        cmd = _convert_instruction_to_cmd(inst, i, instructions)
        if cmd:
            cmd_block.add_cmd(cmd)

    sub.set_command_block(cmd_block)

    # Find return
    for i in range(start_idx, min(end_idx, len(instructions))):
        if instructions[i].ins_type == NCSInstructionType.RETN:
            ret = _convert_retn(instructions[i], i)
            if ret:
                sub.set_return(ret)
            break

    return sub


def _convert_instruction_to_cmd(inst: NCSInstruction, pos: int, instructions: list[NCSInstruction] | None = None):
    """Convert a single NCSInstruction to an AST command node."""
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type

    if ins_type in {NCSInstructionType.CONSTI, NCSInstructionType.CONSTF, NCSInstructionType.CONSTS, NCSInstructionType.CONSTO}:
        return _convert_const_cmd(inst, pos)
    elif ins_type == NCSInstructionType.ACTION:
        return _convert_action_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.JMP, NCSInstructionType.JSR, NCSInstructionType.JZ, NCSInstructionType.JNZ}:
        return _convert_jump_cmd(inst, pos, instructions)
    elif ins_type == NCSInstructionType.RETN:
        return _convert_retn_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.CPDOWNSP, NCSInstructionType.CPTOPSP}:
        return _convert_copy_sp_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.CPDOWNBP, NCSInstructionType.CPTOPBP}:
        return _convert_copy_bp_cmd(inst, pos)
    elif ins_type == NCSInstructionType.MOVSP:
        return _convert_movesp_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.RSADDI, NCSInstructionType.RSADDF, NCSInstructionType.RSADDS, NCSInstructionType.RSADDO}:
        return _convert_rsadd_cmd(inst, pos)
    elif ins_type == NCSInstructionType.DESTRUCT:
        return _convert_destruct_cmd(inst, pos)
    elif ins_type in {NCSInstructionType.SAVEBP, NCSInstructionType.RESTOREBP}:
        return _convert_bp_cmd(inst, pos)
    elif ins_type == NCSInstructionType.STORE_STATE:
        return _convert_store_state_cmd(inst, pos)
    # Add binary/unary/logic ops...

    return None


def _convert_const_cmd(inst: NCSInstruction, pos: int):
    """Convert CONST instruction to AConstCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_const_cmd import AConstCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_const_command import AConstCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_const import TConst  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_int_constant import AIntConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_float_constant import AFloatConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_string_constant import AStringConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_float_constant import TFloatConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_string_literal import TStringLiteral  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]

    const_cmd = AConstCmd()
    const_command = AConstCommand()

    const_command.set_const(TConst(pos, 0))
    const_command.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    const_command.set_type(TIntegerConstant(str(type_val), pos, 0))

    if inst.args:
        if ins_type == NCSInstructionType.CONSTI:
            int_val = inst.args[0] if len(inst.args) > 0 else 0
            const_constant = AIntConstant()
            const_constant.set_integer_constant(TIntegerConstant(str(int_val), pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTF:
            float_val = inst.args[0] if len(inst.args) > 0 else 0.0
            const_constant = AFloatConstant()
            const_constant.set_float_constant(TFloatConstant(str(float_val), pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTS:
            str_val = inst.args[0] if len(inst.args) > 0 else ""
            const_constant = AStringConstant()
            const_constant.set_string_literal(TStringLiteral(f'"{str_val}"', pos, 0))
            const_command.set_constant(const_constant)
        elif ins_type == NCSInstructionType.CONSTO:
            obj_val = inst.args[0] if len(inst.args) > 0 else 0
            const_constant = AIntConstant()
            const_constant.set_integer_constant(TIntegerConstant(str(obj_val), pos, 0))
            const_command.set_constant(const_constant)

    const_command.set_semi(TSemi(pos, 0))
    const_cmd.set_const_command(const_command)

    return const_cmd


def _convert_action_cmd(inst: NCSInstruction, pos: int):
    """Convert ACTION instruction to AActionCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_action_cmd import AActionCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_action_command import AActionCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_action import TAction  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    action_cmd = AActionCmd()
    action_command = AActionCommand()

    action_command.set_action(TAction(pos, 0))
    action_command.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    action_command.set_type(TIntegerConstant(str(type_val), pos, 0))
    
    # ACTION args: [routine_id (uint16), arg_count (uint8)]
    id_val = 0
    arg_count_val = 0
    if inst.args and len(inst.args) >= 1:
        id_val = inst.args[0] if len(inst.args) > 0 else 0
        arg_count_val = inst.args[1] if len(inst.args) > 1 else 0

    action_command.set_id(TIntegerConstant(str(id_val), pos, 0))
    action_command.set_arg_count(TIntegerConstant(str(arg_count_val), pos, 0))
    action_command.set_semi(TSemi(pos, 0))

    action_cmd.set_action_command(action_command)

    return action_cmd


def _convert_jump_cmd(inst: NCSInstruction, pos: int, instructions: list[NCSInstruction] | None = None):
    """Convert JMP/JSR/JZ/JNZ instruction to appropriate cmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_jump_cmd import AJumpCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_sub_cmd import AJumpSubCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_command import AJumpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_jump_to_subroutine import AJumpToSubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jmp import TJmp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_jsr import TJsr  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    
    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    offset = 0
    if inst.jump is not None and instructions is not None:
        try:
            jump_idx = instructions.index(inst.jump)
            offset = jump_idx - pos
        except ValueError:
            offset = 0

    if ins_type == NCSInstructionType.JSR:
        jsr_cmd = AJumpSubCmd()
        jsr_to_sub = AJumpToSubroutine()

        jsr_to_sub.set_jsr(TJsr(pos, 0))
        jsr_to_sub.set_pos(TIntegerConstant(str(pos), pos, 0))
        jsr_to_sub.set_type(TIntegerConstant(str(type_val), pos, 0))
        jsr_to_sub.set_offset(TIntegerConstant(str(offset), pos, 0))
        jsr_to_sub.set_semi(TSemi(pos, 0))

        jsr_cmd.set_jump_to_subroutine(jsr_to_sub)
        return jsr_cmd
    else:
        jump_cmd = AJumpCmd()
        jump_command = AJumpCommand()

        jump_command.set_jmp(TJmp(pos, 0))
        jump_command.set_pos(TIntegerConstant(str(pos), pos, 0))
        jump_command.set_type(TIntegerConstant(str(type_val), pos, 0))
        jump_command.set_offset(TIntegerConstant(str(offset), pos, 0))
        jump_command.set_semi(TSemi(pos, 0))

        jump_cmd.set_jump_command(jump_command)
        return jump_cmd


def _convert_retn(inst: NCSInstruction, pos: int):
    """Convert RETN instruction to AReturn (for subroutine return)."""
    from pykotor.resource.formats.ncs.dencs.node.a_return import AReturn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_retn import TRetn  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    
    ret = AReturn()
    ret.set_retn(TRetn(pos, 0))
    ret.set_pos(TIntegerConstant(str(pos), pos, 0))

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    ret.set_type(TIntegerConstant(str(type_val), pos, 0))
    ret.set_semi(TSemi(pos, 0))

    return ret


def _convert_retn_cmd(inst: NCSInstruction, pos: int):
    """Convert RETN instruction to AReturnCmd (for command block)."""
    from pykotor.resource.formats.ncs.dencs.node.a_return_cmd import AReturnCmd  # pyright: ignore[reportMissingImports]
    
    retn_cmd = AReturnCmd()
    retn = _convert_retn(inst, pos)
    retn_cmd.set_return(retn)

    return retn_cmd


def _convert_copy_sp_cmd(inst: NCSInstruction, pos: int):
    """Convert CPDOWNSP/CPTOPSP instruction to appropriate cmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_copydownsp_cmd import ACopydownspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copytopsp_cmd import ACopytopspCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_down_sp_command import ACopyDownSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_copy_top_sp_command import ACopyTopSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cpdownsp import TCpdownsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_cptopsp import TCptopsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.ncs_data import NCSInstructionType  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0
    size = inst.args[1] if inst.args and len(inst.args) > 1 else 0

    if ins_type == NCSInstructionType.CPDOWNSP:
        cmd = ACopydownspCmd()
        command = ACopyDownSpCommand()
        command.set_cpdownsp(TCpdownsp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_down_sp_command(command)
        return cmd
    else:  # CPTOPSP
        cmd = ACopytopspCmd()
        command = ACopyTopSpCommand()
        command.set_cptopsp(TCptopsp(pos, 0))
        command.set_pos(TIntegerConstant(str(pos), pos, 0))
        command.set_type(TIntegerConstant(str(type_val), pos, 0))
        command.set_offset(TIntegerConstant(str(offset), pos, 0))
        command.set_size(TIntegerConstant(str(size), pos, 0))
        command.set_semi(TSemi(pos, 0))
        cmd.set_copy_top_sp_command(command)
        return cmd


def _convert_copy_bp_cmd(inst: NCSInstruction, pos: int):
    """Convert CPDOWNBP/CPTOPBP instruction to appropriate cmd."""
    return None


def _convert_movesp_cmd(inst: NCSInstruction, pos: int):
    """Convert MOVSP instruction to AMovespCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_movesp_cmd import AMovespCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_move_sp_command import AMoveSpCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_movsp import TMovsp  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0
    offset = inst.args[0] if inst.args and len(inst.args) > 0 else 0

    cmd = AMovespCmd()
    command = AMoveSpCommand()
    command.set_movsp(TMovsp(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_offset(TIntegerConstant(str(offset), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_move_sp_command(command)

    return cmd


def _convert_rsadd_cmd(inst: NCSInstruction, pos: int):
    """Convert RSADD instruction to ARsaddCmd."""
    from pykotor.resource.formats.ncs.dencs.node.a_rsadd_cmd import ARsaddCmd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_rsadd_command import ARsaddCommand  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_rsadd import TRsadd  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_integer_constant import TIntegerConstant  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.t_semi import TSemi  # pyright: ignore[reportMissingImports]

    ins_type = inst.ins_type
    type_val = ins_type.value.qualifier if hasattr(ins_type, 'value') and hasattr(ins_type.value, 'qualifier') else 0

    cmd = ARsaddCmd()
    command = ARsaddCommand()
    command.set_rsadd(TRsadd(pos, 0))
    command.set_pos(TIntegerConstant(str(pos), pos, 0))
    command.set_type(TIntegerConstant(str(type_val), pos, 0))
    command.set_semi(TSemi(pos, 0))
    cmd.set_rsadd_command(command)

    return cmd


def _convert_destruct_cmd(inst: NCSInstruction, pos: int):
    """Placeholder - needs full implementation"""
    return None


def _convert_bp_cmd(inst: NCSInstruction, pos: int):
    """Placeholder - needs full implementation"""
    return None


def _convert_store_state_cmd(inst: NCSInstruction, pos: int):
    """Placeholder - needs full implementation"""
    return None

