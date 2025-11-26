from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_expression import AExpression  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptnode.a_switch_case import ASwitchCase  # pyright: ignore[reportMissingImports]


class ASwitch(ScriptNode):
    def __init__(self, start: int, switchexp: AExpression):
        from pykotor.resource.formats.ncs.dencs.scriptnode.script_node import ScriptNode  # pyright: ignore[reportMissingImports]
        super().__init__()
        self.start: int = start
        self.cases: list[ASwitchCase] = []
        self.defaultcase: ASwitchCase | None = None
        self.switch_exp(switchexp)

    def switch_exp(self, switchexp: AExpression):
        switchexp.parent(self)  # type: ignore
        self.switchexp: AExpression = switchexp

    def switch_exp(self) -> AExpression:
        return self.switchexp

    def end(self, end: int):
        self.end_val = end
        if self.defaultcase is not None:
            self.defaultcase.end(end)
        elif len(self.cases) > 0:
            self.cases[-1].end(end)

    def end(self) -> int:
        return getattr(self, 'end_val', -1)

    def add_case(self, acase: ASwitchCase):
        acase.parent(self)  # type: ignore
        self.cases.append(acase)

    def add_default_case(self, acase: ASwitchCase):
        acase.parent(self)  # type: ignore
        self.defaultcase = acase

    def get_last_case(self) -> ASwitchCase | None:
        if len(self.cases) == 0:
            return None
        return self.cases[-1]

    def get_next_case(self, lastcase: ASwitchCase | None) -> ASwitchCase | None:
        if lastcase is None:
            return self.get_first_case()
        if lastcase == self.defaultcase:
            return None
        try:
            index = self.cases.index(lastcase) + 1
        except ValueError:
            raise RuntimeError("invalid last case passed in")
        if len(self.cases) > index:
            return self.cases[index]
        return self.defaultcase

    def get_first_case(self) -> ASwitchCase | None:
        if len(self.cases) > 0:
            return self.cases[0]
        return self.defaultcase

    def get_first_case_start(self) -> int:
        if len(self.cases) > 0:
            return self.cases[0].get_start()
        if self.defaultcase is not None:
            return self.defaultcase.get_start()
        return -1

    def __str__(self) -> str:
        buff = []
        buff.append(self.tabs + "switch (" + str(self.switchexp) + ") {" + self.newline)
        for case in self.cases:
            buff.append(str(case))
        if self.defaultcase is not None:
            buff.append(str(self.defaultcase))
        buff.append(self.tabs + "}" + self.newline)
        return "".join(buff)

    def close(self):
        super().close()
        if self.cases is not None:
            for case in self.cases:
                case.close()
        self.cases = None
        if self.defaultcase is not None:
            self.defaultcase.close()
        self.defaultcase = None
        if self.switchexp is not None:
            self.switchexp.close()  # type: ignore
        self.switchexp = None

