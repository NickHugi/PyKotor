from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.formats.ncs.dencs.utils.subroutine_analysis_data import SubroutineAnalysisData  # pyright: ignore[reportMissingImports]
    from pykotor.resource.formats.ncs.dencs.scriptutils.sub_script_state import SubScriptState  # pyright: ignore[reportMissingImports]


class FileScriptData:
    def __init__(self):
        self.subs: list[SubScriptState] = []
        self.globals: SubScriptState | None = None
        self.subdata: SubroutineAnalysisData | None = None
        self.status: int = 0
        self.code: str | None = None
        self.originalbytecode: str | None = None
        self.generatedbytecode: str | None = None

    def close(self):
        for sub in self.subs:
            sub.close()
        self.subs = None
        if self.globals is not None:
            self.globals.close()
            self.globals = None
        if self.subdata is not None:
            self.subdata.close()
            self.subdata = None
        self.code = None
        self.originalbytecode = None
        self.generatedbytecode = None

    def globals(self, globals: SubScriptState):
        self.globals = globals

    def add_sub(self, sub: SubScriptState):
        self.subs.append(sub)

    def subdata(self, subdata: SubroutineAnalysisData):
        self.subdata = subdata

    def find_sub(self, name: str) -> SubScriptState | None:
        for state in self.subs:
            if state.get_name() == name:
                return state
        return None

    def replace_sub_name(self, oldname: str, newname: str) -> bool:
        state = self.find_sub(oldname)
        if state is None:
            return False
        if self.find_sub(newname) is not None:
            return False
        state.set_name(newname)
        self.generate_code()
        state = None
        return True

    def __str__(self) -> str:
        return self.code if self.code is not None else ""

    def get_vars(self) -> dict[str, list] | None:
        if len(self.subs) == 0:
            return None
        vars: dict[str, list] = {}
        for state in self.subs:
            vars[state.get_name()] = state.get_variables()
        if self.globals is not None:
            vars["GLOBALS"] = self.globals.get_variables()
        return vars

    def get_code(self) -> str | None:
        return self.code

    def set_code(self, code: str):
        self.code = code

    def get_original_byte_code(self) -> str | None:
        return self.originalbytecode

    def set_original_byte_code(self, obcode: str):
        self.originalbytecode = obcode

    def get_new_byte_code(self) -> str | None:
        return self.generatedbytecode

    def set_new_byte_code(self, nbcode: str):
        self.generatedbytecode = nbcode

    def generate_code(self):
        try:
            if len(self.subs) == 0:
                return
            newline = os.linesep
            protobuff: list[str] = []
            fcnbuff: list[str] = []
            for state in self.subs:
                if not state.is_main():
                    protobuff.append(str(state.get_proto()) + ";" + newline)
                fcnbuff.append(str(state) + newline)
            globs = ""
            if self.globals is not None:
                globs = "// Globals" + newline + state.to_string_globals() + newline
            protohdr = ""
            if len(protobuff) > 0:
                protohdr = "// Prototypes" + newline
                protobuff.append(newline)
            self.code = str(self.subdata.get_struct_declarations()) + globs + protohdr + "".join(protobuff) + "".join(fcnbuff)
        finally:
            protobuff = None
            fcnbuff = None
            state = None
        protobuff = None
        fcnbuff = None
        state = None

