from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]


class Action:
    def __init__(self, type_str: str, name: str, params: str):
        self.name = name
        from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
        self.returntype = Type.parse_type(type_str)
        self.paramlist = []
        self.paramsize = 0
        p = re.compile(r"\s*(\w+)\s+\w+(\s*=\s*\S+)?\s*")
        tokens = params.split(",")
        for token in tokens:
            m = p.match(token)
            if m:
                from pykotor.resource.formats.ncs.dencs.utils.type import Type  # pyright: ignore[reportMissingImports]
                self.paramlist.append(Type(m.group(1)))
                self.paramsize += Type.type_size(m.group(1))

    def __str__(self) -> str:
        return "\"" + self.name + "\" " + self.returntype.to_value_string() + " " + str(self.paramsize)

    def params(self):
        return self.paramlist

    def return_type(self):
        return self.returntype

    def paramsize(self) -> int:
        return self.paramsize

    def name(self) -> str:
        return self.name


class ActionsData:
    def __init__(self, actionsreader):
        self.actionsreader = actionsreader
        self.actions = []
        self.read_actions()

    def get_action(self, index: int) -> str:
        try:
            action = self.actions[index]
            return str(action)
        except IndexError:
            raise RuntimeError("Invalid action call: action " + str(index))

    def read_actions(self):
        p = re.compile(r"^\s*(\w+)\s+(\w+)\s*\((.*)\).*")
        self.actions = []
        while True:
            str_line = self.actionsreader.readline()
            if str_line is None:
                continue
            if str_line.startswith("// 0"):
                while True:
                    str_line = self.actionsreader.readline()
                    if str_line is None:
                        break
                    if str_line.startswith("//"):
                        continue
                    if len(str_line) == 0:
                        continue
                    m = p.match(str_line)
                    if not m:
                        continue
                    self.actions.append(Action(m.group(1), m.group(2), m.group(3)))
                print("read actions.  There were " + str(len(self.actions)))
                return

    def get_return_type(self, index: int):
        return self.actions[index].return_type()

    def get_name(self, index: int) -> str:
        return self.actions[index].name()

    def get_param_types(self, index: int):
        return self.actions[index].params()

