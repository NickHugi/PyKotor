from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_type_stack import LocalTypeStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_analysis_data import NodeAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]


class SubroutineState:
    PROTO_NO = 0
    PROTO_IN_PROGRESS = 1
    PROTO_DONE = 2
    JUMP_YES = 0
    JUMP_NO = 1
    JUMP_NA = 2

    class DecisionData:
        def __init__(self, node: Node, destination: int, forcejump: bool):
            if forcejump:
                self.decision: int = 2
            else:
                self.decision: int = 1
            self.decisionnode: Node = node
            self.destination: int = destination

        def do_jump(self) -> bool:
            return self.decision != 1

        def switch_decision(self) -> bool:
            if self.decision == 1:
                self.decision = 0
                return True
            return False

        def close(self):
            self.decisionnode = None

    def __init__(self, nodedata: NodeAnalysisData, root: Node, id_val: int):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.nodedata: NodeAnalysisData = nodedata
        self.params: list[Type] = []
        self.decisionqueue: list[SubroutineState.DecisionData] = []
        self.paramstyped: bool = True
        self.paramsize: int = 0
        self.status: int = 0
        self.type: Type = Type(0)
        self.root: Node = root
        self.id: int = id_val
        self.returndepth: int = 0

    def parse_done(self):
        self.root = None
        self.nodedata = None
        self.decisionqueue = None

    def close(self):
        if self.decisionqueue is not None:
            for decision in self.decisionqueue:
                decision.close()
        self.decisionqueue = None
        self.params = None
        self.root = None
        self.nodedata = None
        if self.type is not None:
            self.type.close()
        self.type = None

    def print_state(self):
        print("Return type is " + str(self.type))
        print("There are " + str(self.paramsize) + " parameters")
        if self.paramsize > 0:
            buff = []
            buff.append(" Types: ")
            for param in self.params:
                buff.append(str(param) + " ")
            print("".join(buff))

    def print_decisions(self):
        print("-----------------------------")
        print("Jump Decisions")
        for i, data in enumerate(self.decisionqueue):
            str_parts = []
            str_parts.append("  (" + str(i + 1))
            str_parts.append(") at pos " + str(self.nodedata.get_pos(data.decisionnode)))
            if data.decision == 0:
                str_parts.append(" do optional jump to ")
            elif data.decision == 2:
                str_parts.append(" do required jump to ")
            else:
                str_parts.append(" do not jump to ")
            str_parts.append(str(data.destination))
            print("".join(str_parts))

    def __str__(self, main: bool = False) -> str:
        buff = []
        buff.append(str(self.type) + " ")
        if main:
            buff.append("main(")
        else:
            buff.append("sub" + str(self.id) + "(")
        link = ""
        for i in range(self.paramsize):
            ptype = self.params[i]
            buff.append(link + ptype.to_decl_string() + " param" + str(i))
            link = ", "
        buff.append(")")
        return "".join(buff)

    def start_prototyping(self):
        self.status = 1

    def stop_prototyping(self, success: bool):
        if success:
            self.status = 2
            self.decisionqueue = None
        else:
            self.status = 0

    def is_prototyped(self) -> bool:
        return self.status == 2

    def is_being_prototyped(self) -> bool:
        return self.status == 1

    def is_totally_prototyped(self) -> bool:
        return self.status == 2 and self.paramstyped and self.type.is_typed()

    def get_skip_start(self, pos: int) -> bool:
        if self.decisionqueue is None or len(self.decisionqueue) == 0:
            return False
        decision = self.decisionqueue[0]
        if self.nodedata.get_pos(decision.decisionnode) == pos:
            if decision.do_jump():
                return True
            self.decisionqueue.pop(0)
        return False

    def get_skip_end(self, pos: int) -> bool:
        if len(self.decisionqueue) == 0:
            return False
        if self.decisionqueue[0].destination == pos:
            self.decisionqueue.pop(0)
            return True
        return False

    def set_param_count(self, params: int):
        self.paramsize = params
        if params > 0:
            self.paramstyped = False
            if self.returndepth <= params:
                from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
                self.type = Type(0)

    def get_param_count(self) -> int:
        return self.paramsize

    def type(self) -> Type:
        return self.type

    def params(self) -> list[Type]:
        return self.params

    def set_return_type(self, type_val: Type, depth: int):
        self.type = type_val
        self.returndepth = depth

    def update_params(self, types: list[Type]):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.paramstyped = True
        redo = len(self.params) > 0
        if len(types) != self.paramsize:
            raise RuntimeError("Parameter count does not match: expected " + str(self.paramsize) + " and got " + str(len(types)))
        for i in range(len(types)):
            newtype = types[i]
            if redo and not self.params[i].is_typed():
                self.params[i] = newtype
            elif not redo:
                self.params.append(newtype)
            if not self.params[i].is_typed():
                self.paramstyped = False

    def get_param_type(self, pos: int) -> Type:
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        if len(self.params) < pos:
            return Type(0)
        return self.params[pos - 1]

    def init_stack(self, stack: LocalTypeStack):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
        if self.is_prototyped():
            if self.type.is_typed() and not self.type.equals(0):
                if isinstance(self.type, StructType):
                    structtypes = self.type.types()
                    for structtype in structtypes:
                        stack.push(structtype)
                else:
                    stack.push(self.type)
            if self.paramsize == len(self.params):
                for j in range(self.paramsize):
                    stack.push(self.params[j])
            else:
                for j in range(self.paramsize):
                    stack.push(Type(-1))

    def init_stack(self, stack: LocalVarStack):
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]
        if not self.type.equals(0):
            if isinstance(self.type, StructType):
                retvar = VarStruct(self.type)
            else:
                retvar = Variable(self.type)
            retvar.is_return(True)
            stack.push(retvar)
        for i in range(self.paramsize):
            paramvar = Variable(self.params[i])
            paramvar.is_param(True)
            stack.push(paramvar)

    def get_id(self) -> int:
        return self.id

    def get_start(self) -> int:
        return self.nodedata.get_pos(self.root)

    def get_end(self) -> int:
        from pykotor.resource.formats.ncs.dencs.utils.node_utils import NodeUtils  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.node.a_subroutine import ASubroutine  # pyright: ignore[reportMissingImports]
        return NodeUtils.get_sub_end(self.root)

    def add_decision(self, node: Node, destination: int):
        decision = SubroutineState.DecisionData(node, destination, False)
        self.decisionqueue.append(decision)
        if len(self.decisionqueue) > 3000:
            raise RuntimeError("Decision queue size over 3000 - probable infinite loop")

    def add_jump(self, node: Node, destination: int):
        decision = SubroutineState.DecisionData(node, destination, True)
        self.decisionqueue.append(decision)

    def get_current_destination(self) -> int:
        if len(self.decisionqueue) == 0:
            raise RuntimeError("Attempted to get a destination but no decision nodes found.")
        data = self.decisionqueue[-1]
        return data.destination

    def switch_decision(self) -> int:
        while len(self.decisionqueue) > 0:
            data = self.decisionqueue[-1]
            if data.switch_decision():
                return data.destination
            self.decisionqueue.pop()
        return -1

