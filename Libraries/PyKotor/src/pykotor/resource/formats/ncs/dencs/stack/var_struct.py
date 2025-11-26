from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]


class VarStruct(Variable):
    def __init__(self, structtype: StructType | None = None):
        from pykotor.resource.formats.ncs.dencs.stack.variable import Variable  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.struct_type import StructType  # pyright: ignore[reportMissingImports]
        super().__init__(Type(-15))
        self.vars: list[Variable] = []
        self.size = 0
        if structtype is None:
            self.structtype = StructType()
        else:
            self.structtype = structtype
            for type in structtype.types():
                if isinstance(type, StructType):
                    self.add_var(VarStruct(type))
                else:
                    self.add_var(Variable(type))

    def close(self):
        super().close()
        if self.vars is not None:
            for var in self.vars:
                var.close()
        self.vars = None
        if self.structtype is not None:
            self.structtype.close()
        self.structtype = None

    def add_var(self, var: Variable):
        self.vars.insert(0, var)
        var.varstruct(self)
        self.structtype.add_type(var.type())
        self.size += var.size()

    def add_var_stack_order(self, var: Variable):
        self.vars.append(var)
        var.varstruct(self)
        self.structtype.add_type_stack_order(var.type())
        self.size += var.size()

    def name(self, prefix: str, count: int):
        self.name = prefix + "struct" + str(count)

    def name(self) -> str:
        return self.name

    def struct_type(self, structtype: StructType):
        self.structtype = structtype

    def __str__(self) -> str:
        return str(self.name) if self.name is not None else ""

    def type_name(self) -> str:
        return self.structtype.type_name()

    def to_decl_string(self) -> str:
        return str(self.structtype.to_decl_string()) + " " + str(self.name)

    def update_names(self):
        if self.structtype.is_vector():
            self.vars[0].name("z")
            self.vars[1].name("y")
            self.vars[2].name("x")
        else:
            for i in range(len(self.vars)):
                self.vars[i].name(self.structtype.element_name(len(self.vars) - i - 1))

    def assigned(self):
        for var in self.vars:
            var.assigned()

    def added_to_stack(self, stack: LocalStack):
        for var in self.vars:
            var.added_to_stack(stack)

    def contains(self, var: Variable) -> bool:
        return var in self.vars

    def struct_type(self) -> StructType:
        return self.structtype

    def get_element(self, stackpos: int) -> StackEntry:
        pos = 0
        for i in range(len(self.vars) - 1, -1, -1):
            entry = self.vars[i]
            pos += entry.size()
            if pos == stackpos:
                return entry.get_element(1)
            if pos > stackpos:
                return entry.get_element(pos - stackpos + 1)
        raise RuntimeError("Stackpos was greater than stack size")

    def structify(self, firstelement: int, count: int, subdata: SubroutineAnalysisData) -> VarStruct:
        pos = 0
        for i, entry in enumerate(self.vars):
            pos += entry.size()
            if pos == firstelement:
                varstruct = VarStruct()
                varstruct.add_var_stack_order(entry)
                self.vars[i] = varstruct
                j = i + 1
                while j < len(self.vars) and pos <= firstelement + count - 1:
                    entry = self.vars.pop(j)
                    pos += entry.size()
                    varstruct.add_var_stack_order(entry)
                subdata.add_struct(varstruct)
                return varstruct
            if pos == firstelement + count - 1:
                return entry
            if pos > firstelement + count - 1:
                return entry.structify(firstelement - (pos - entry.size()), count, subdata)
        return None

