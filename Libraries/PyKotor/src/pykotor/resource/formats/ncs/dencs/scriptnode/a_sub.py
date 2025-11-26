from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_var_ref import AVarRef  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class ASub(ScriptRootNode):
    def __init__(self, type_val: Type | int, id_val: int | None = None, params: list[AVarRef] | None = None, start: int = 0, end: int = 0):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_root_node import ScriptRootNode  # pyright: ignore[reportMissingImports]
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        super().__init__(start, end)
        if isinstance(type_val, int):
            self.type: Type = Type(type_val)
        else:
            self.type = type_val
        if id_val is not None:
            self.id: int = id_val
            self.params: list[AVarRef] = []
            self.tabs = ""
            if params is not None:
                for param in params:
                    self.add_param(param)
            self.name: str = "sub" + str(id_val)
        else:
            self.type = Type(0)
            self.params = None
            self.tabs = ""

    def add_param(self, param: AVarRef):
        param.parent(self)  # type: ignore
        if self.params is None:
            self.params = []
        self.params.append(param)

    def __str__(self) -> str:
        return self.get_header() + " {" + self.newline + self.get_body() + "}" + self.newline

    def get_body(self) -> str:
        buff = []
        for child in self.children:
            buff.append(str(child))
        return "".join(buff)

    def get_header(self) -> str:
        buff = []
        buff.append(str(self.type) + " " + self.name + "(")
        link = ""
        if self.params is not None:
            for param in self.params:
                ptype = param.type()
                buff.append(link + str(ptype) + " " + str(param))
                link = ", "
        buff.append(")")
        return "".join(buff)

    def is_main(self, ismain: bool):
        self.ismain = ismain
        if ismain:
            if self.type.equals(3):
                self.name = "StartingConditional"
            else:
                self.name = "main"

    def is_main(self) -> bool:
        return getattr(self, 'ismain', False)

    def type(self) -> Type:
        return self.type

    def name(self, name: str):
        self.name = name

    def name(self) -> str:
        return getattr(self, 'name', '')

    def get_param_vars(self) -> list:
        vars_list = []
        if self.params is not None:
            for param in self.params:
                vars_list.append(param.var_var())
        return vars_list

    def close(self):
        super().close()
        if self.params is not None:
            for param in self.params:
                param.close()
        self.params = None
        if self.type is not None:
            self.type.close()
        self.type = None

