from __future__ import annotations

import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.optimizers import RemoveNopOptimizer


class TestNCSOptimizers(unittest.TestCase):
    def compile(
        self,
        script: str,
        library: dict[str, bytes] | None = None,
        library_lookup: str | None = None,
    ) -> NCS:
        nssLexer = NssLexer()
        nssParser = NssParser(
            library=library,
            constants=KOTOR_CONSTANTS,
            functions=KOTOR_FUNCTIONS,
            library_lookup=library_lookup,
        )

        parser = nssParser.parser
        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs

    def test_no_op_optimizer(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value > 0)
                {
                    if (value > 0)
                    {
                        PrintInteger(value);
                        value -= 1;
                    }
                }
            }
        """
        )

        ncs.optimize([RemoveNopOptimizer()])
        ncs.print()

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])


if __name__ == "__main__":
    unittest.main()
