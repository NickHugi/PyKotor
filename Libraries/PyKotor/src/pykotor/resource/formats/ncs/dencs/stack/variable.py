from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.var_struct import VarStruct  # pyright: ignore[reportMissingImports]


class Variable(StackEntry):
    FCN_NORMAL = 0
    FCN_RETURN = 1
    FCN_PARAM = 2

    def __init__(self, type: Type | int):
        from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__()
        if isinstance(type, int):
            self.type = Type(type)
        else:
            self.type = type
        self.varstruct: VarStruct | None = None
        self.assigned: bool = False
        self.size = 1
        self.function: int = 0
        self.stackcounts: dict[LocalStack, int] = {}
        self.name: str | None = None

    def close(self):
        super().close()
        self.stackcounts = None
        self.varstruct = None

    def done_parse(self):
        self.stackcounts = None

    def done_with_stack(self, stack: LocalVarStack):
        if stack in self.stackcounts:
            del self.stackcounts[stack]

    def is_return(self, isreturn: bool):
        if isreturn:
            self.function = 1
        else:
            self.function = 0

    def is_param(self, isparam: bool):
        if isparam:
            self.function = 2
        else:
            self.function = 0

    def is_return(self) -> bool:
        return self.function == 1

    def is_param(self) -> bool:
        return self.function == 2

    def assigned(self):
        self.assigned = True

    def is_assigned(self) -> bool:
        return self.assigned

    def is_struct(self) -> bool:
        return self.varstruct is not None

    def varstruct(self, varstruct: VarStruct):
        self.varstruct = varstruct

    def varstruct(self) -> VarStruct | None:
        return self.varstruct

    def added_to_stack(self, stack: LocalStack):
        count = self.stackcounts.get(stack, 0)
        self.stackcounts[stack] = count + 1

    def removed_from_stack(self, stack: LocalStack):
        count = self.stackcounts.get(stack, 0)
        if count == 0:
            if stack in self.stackcounts:
                del self.stackcounts[stack]
        else:
            self.stackcounts[stack] = count - 1

    def is_placeholder(self, stack: LocalStack) -> bool:
        count = self.stackcounts.get(stack, 0)
        return count == 0 and not self.assigned

    def is_on_stack(self, stack: LocalStack) -> bool:
        count = self.stackcounts.get(stack, 0)
        return count > 0

    def name(self, prefix: str, hint: int):
        self.name = prefix + str(self.type) + str(hint)

    def name(self, infix: str, hint: int):
        self.name = str(self.type) + infix + str(hint)

    def name(self, name: str):
        self.name = name

    def get_element(self, stackpos: int) -> StackEntry:
        if stackpos != 1:
            raise RuntimeError("Position > 1 for var, not struct")
        return self

    def to_debug_string(self) -> str:
        return "type: " + str(self.type) + " name: " + str(self.name) + " assigned: " + str(self.assigned)

    def __str__(self) -> str:
        if self.varstruct is not None:
            self.varstruct.update_names()
            return str(self.varstruct.name()) + "." + str(self.name)
        return str(self.name) if self.name is not None else ""

    def to_decl_string(self) -> str:
        return str(self.type) + " " + str(self.name)

    def stack_was_cloned(self, oldstack: LocalStack, newstack: LocalStack):
        count = self.stackcounts.get(oldstack, 0)
        if count > 0:
            self.stackcounts[newstack] = count

