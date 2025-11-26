from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.start import Start  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.check_is_globals import CheckIsGlobals  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class SubroutineAnalysisData:
    def __init__(self, nodedata: NodeAnalysisData):
        self.nodedata: NodeAnalysisData = nodedata
        self.subroutines: dict[int, object] = {}
        self.substates: dict[object, SubroutineState] = {}
        self.mainsub: ASubroutine | None = None
        self.globalsub: ASubroutine | None = None
        self.globalstack: LocalVarStack | None = None
        self.globalstructs: list[StructType] = []
        self.globalstate: SubScriptState | None = None
        self.result: bool = False

    def parse_done(self):
        self.nodedata = None
        if self.substates is not None:
            for state in self.substates.values():
                state.parse_done()
            self.substates = None
        self.subroutines = None
        self.mainsub = None
        self.globalsub = None
        self.globalstate = None

    def close(self):
        if self.nodedata is not None:
            self.nodedata.close()
            self.nodedata = None
        if self.substates is not None:
            for state in self.substates.values():
                state.close()
            self.substates = None
        if self.subroutines is not None:
            self.subroutines.clear()
            self.subroutines = None
        self.mainsub = None
        self.globalsub = None
        if self.globalstack is not None:
            self.globalstack.close()
            self.globalstack = None
        if self.globalstructs is not None:
            for struct in self.globalstructs:
                struct.close()
            self.globalstructs = None
        if self.globalstate is not None:
            self.globalstate.close()
            self.globalstate = None

    def print_states(self):
        for node, state in self.substates.items():
            print("Printing state for subroutine at " + str(self.nodedata.get_pos(node)))
            state.print_state()

    def global_state(self) -> SubScriptState | None:
        return self.globalstate

    def global_state(self, globalstate: SubScriptState):
        self.globalstate = globalstate

    def get_globals_sub(self) -> ASubroutine | None:
        return self.globalsub

    def set_globals_sub(self, globalsub: ASubroutine):
        self.globalsub = globalsub

    def get_main_sub(self) -> ASubroutine | None:
        return self.mainsub

    def set_main_sub(self, mainsub: ASubroutine):
        self.mainsub = mainsub

    def get_global_stack(self) -> LocalVarStack | None:
        return self.globalstack

    def set_global_stack(self, stack: LocalVarStack):
        self.globalstack = stack

    def num_subs(self) -> int:
        return len(self.subroutines)

    def count_subs_done(self) -> int:
        count = 0
        for state in self.substates.values():
            if state.is_totally_prototyped():
                count += 1
        return count

    def get_state(self, sub: object) -> SubroutineState | None:
        state = self.substates.get(sub)
        return state

    def is_prototyped(self, pos: int, nullok: bool) -> bool:
        sub = self.subroutines.get(pos)
        if sub is not None:
            state = self.substates.get(sub)
            return state is not None and state.is_prototyped()
        if nullok:
            return False
        raise RuntimeError("Checking prototype on a subroutine not in the hash")

    def is_being_prototyped(self, pos: int) -> bool:
        sub = self.subroutines.get(pos)
        if sub is None:
            raise RuntimeError("Checking prototype on a subroutine not in the hash")
        state = self.substates.get(sub)
        return state is not None and state.is_being_prototyped()

    def is_fully_prototyped(self, pos: int) -> bool:
        sub = self.subroutines.get(pos)
        if sub is None:
            raise RuntimeError("Checking prototype on a subroutine not in the hash")
        state = self.substates.get(sub)
        return state is not None and state.is_totally_prototyped()

    def add_struct(self, struct: StructType):
        if struct not in self.globalstructs:
            self.globalstructs.append(struct)
            struct.type_name("structtype" + str(len(self.globalstructs)))

    def add_struct(self, struct: VarStruct):
        structtype = struct.struct_type()
        if structtype not in self.globalstructs:
            self.globalstructs.append(structtype)
            structtype.type_name("structtype" + str(len(self.globalstructs)))
        else:
            struct.struct_type(self.get_struct_prototype(structtype))

    def get_struct_declarations(self) -> str:
        newline = os.linesep
        buff: list[str] = []
        for i in range(len(self.globalstructs)):
            structtype = self.globalstructs[i]
            if not structtype.is_vector():
                buff.append(str(structtype.to_decl_string()) + " {" + newline)
                types = structtype.types()
                for j in range(len(types)):
                    buff.append("\t" + types[j].to_decl_string() + " " + structtype.element_name(j) + ";" + newline)
                buff.append("};" + newline + newline)
                types = None
        return "".join(buff)

    def get_struct_type_name(self, structtype: StructType) -> str:
        protostruct = self.get_struct_prototype(structtype)
        return protostruct.type_name()

    def get_struct_prototype(self, structtype: StructType) -> StructType:
        try:
            index = self.globalstructs.index(structtype)
        except ValueError:
            self.globalstructs.append(structtype)
            index = len(self.globalstructs) - 1
        return self.globalstructs[index]

    def add_subroutine(self, pos: int, node: object, id: int):
        self.subroutines[pos] = node
        self.add_sub_state(node, id)

    def add_sub_state(self, sub: object, id: int):
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
        state = SubroutineState(self.nodedata, sub, id)
        self.substates[sub] = state

    def add_sub_state(self, sub: object, id: int, type: Type):
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_state import SubroutineState  # pyright: ignore[reportMissingImports]
        state = SubroutineState(self.nodedata, sub, id)
        state.set_return_type(type, 1)
        self.substates[sub] = state

    def add_main(self, sub: ASubroutine, conditional: bool):
        self.mainsub = sub
        if conditional:
            from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
            self.add_sub_state(self.mainsub, 0, Type(3))
        else:
            self.add_sub_state(self.mainsub, 0)

    def add_globals(self, sub: ASubroutine):
        self.globalsub = sub

    def get_subroutines(self):
        from pykotor.resource.formats.ncs.dencs.utils.subroutine_iterator import SubroutineIterator  # pyright: ignore[reportMissingImports]
        subs: list[object] = []
        keys = sorted(self.subroutines.keys(), reverse=True)
        for key in keys:
            subs.append(self.subroutines[key])
        return SubroutineIterator(subs)

    def split_off_subroutines(self, ast: Start):
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        conditional = NodeUtils.is_conditional_program(ast)
        from pykotor.resource.formats.ncs.dencs.node.a_program import AProgram  # pyright: ignore[reportMissingImports]
        subroutines = AProgram(ast.get_p_program()).get_subroutine()
        node = subroutines.pop(0)
        if len(subroutines) > 0 and self.is_globals_sub(node):
            self.add_globals(node)
            node = subroutines.pop(0)
        self.add_main(node, conditional)
        id = 1
        while len(subroutines) > 0:
            node = subroutines.pop(0)
            pos = self.nodedata.get_pos(node)
            node2 = node
            id2 = id
            id = id2 + 1
            self.add_subroutine(pos, node2, id2)
        subroutines = None
        node = None

    def is_globals_sub(self, node: ASubroutine) -> bool:
        from pykotor.resource.formats.ncs.dencs.utils.check_is_globals import CheckIsGlobals  # pyright: ignore[reportMissingImports]
        cig = CheckIsGlobals()
        node.apply(cig)
        return cig.get_is_globals()

