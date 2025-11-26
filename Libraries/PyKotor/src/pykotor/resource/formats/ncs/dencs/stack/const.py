from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.stack.stack_entry import StackEntry  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_stack import LocalStack  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.stack.local_var_stack import LocalVarStack  # pyright: ignore[reportMissingImports]


class Const(StackEntry):
    @staticmethod
    def new_const(type: Type, value: object) -> Const:
        if type.byte_value() == 3:
            from pykotor.resource.formats.ncs.dencs.stack.int_const import IntConst  # pyright: ignore[reportMissingImports]
            return IntConst(value)
        elif type.byte_value() == 4:
            from pykotor.resource.formats.ncs.dencs.stack.float_const import FloatConst  # pyright: ignore[reportMissingImports]
            return FloatConst(value)
        elif type.byte_value() == 5:
            from pykotor.resource.formats.ncs.dencs.stack.string_const import StringConst  # pyright: ignore[reportMissingImports]
            return StringConst(value)
        elif type.byte_value() == 6:
            from pykotor.resource.formats.ncs.dencs.stack.object_const import ObjectConst  # pyright: ignore[reportMissingImports]
            return ObjectConst(value)
        else:
            raise RuntimeError("Invalid const type " + str(type))

    def removed_from_stack(self, stack: LocalStack):
        pass

    def added_to_stack(self, stack: LocalStack):
        pass

    def done_parse(self):
        pass

    def done_with_stack(self, stack: LocalVarStack):
        pass

    def __str__(self) -> str:
        return ""

    def get_element(self, stackpos: int) -> StackEntry:
        if stackpos != 1:
            raise RuntimeError("Position > 1 for const, not struct")
        return self

