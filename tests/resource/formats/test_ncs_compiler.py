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
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)


from pathlib import Path

from pykotor.common.geometry import Vector3
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.resource.formats.ncs import NCS, NCSInstructionType
from pykotor.resource.formats.ncs.compiler.classes import CompileError
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")


class TestNSSCompiler(unittest.TestCase):
    def compile(
        self,
        script: str,
        library: dict[str, bytes] | None = None,
        library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None = None,
    ) -> NCS:
        if library is None:
            library = {}
        nssLexer = NssLexer()
        nssParser = NssParser(library=library, constants=KOTOR_CONSTANTS, functions=KOTOR_FUNCTIONS, library_lookup=library_lookup)

        parser = nssParser.parser
        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs

    # region Engine Call
    def test_enginecall(self):
        ncs = self.compile(
            """
            void main()
            {
                object oExisting = GetExitingObject();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1

        assert interpreter.action_snapshots[0].function_name == "GetExitingObject"
        assert interpreter.action_snapshots[0].arg_values == []

    def test_enginecall_return_value(self):
        ncs = self.compile(
            """
            void main()
            {
                int inescapable = GetAreaUnescapable();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("GetAreaUnescapable", lambda: 10)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 10

    def test_enginecall_with_params(self):
        ncs = self.compile(
            """
            void main()
            {
                string tag = "something";
                int n = 15;
                object oSomething = GetObjectByTag(tag, n);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1

        assert interpreter.action_snapshots[0].function_name == "GetObjectByTag"
        assert interpreter.action_snapshots[0].arg_values == ["something", 15]

    def test_enginecall_with_default_params(self):
        ncs = self.compile(
            """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag(tag);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_enginecall_with_missing_params(self):
        script = """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag();
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_enginecall_with_too_many_params(self):
        script = """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag("", 0, "shouldnotbehere");
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_enginecall_delay_command_1(self):
        ncs = self.compile(
            """
            void main()
            {
                object oFirstPlayer = GetFirstPC();
                DelayCommand(1.0, GiveXPToCreature(oFirstPlayer, 9001));
            }
        """
        )

    def test_enginecall_GetFirstObjectInShape_defaults(self):
        # Tests defaults for (int, int, vector)
        ncs = self.compile(
            """
            void main()
            {
                int nShape = SHAPE_CUBE;
                float fSize = 0.0;
                location lTarget;
                GetFirstObjectInShape(nShape, fSize, lTarget);
            }
        """
        )

    def test_enginecall_GetFactionEqual(self):
        # Tests defaults for (object)
        ncs = self.compile(
            """
            void main()
            {
                object oFirst;
                GetFactionEqual(oFirst);
            }
        """
        )

    # endregion

    # region Operators
    def test_addop_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 10 + 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 15

    def test_addop_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0 + 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 15.0

    def test_addop_string_string(self):
        ncs = self.compile(
            """
            void main()
            {
                string value = "abc" + "def";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == "abcdef"

    def test_subop_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 10 - 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5

    def test_subop_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0 - 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5.0

    def test_mulop_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 * 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 50

    def test_mulop_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float a = 10.0 * 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 50.0

    def test_divop_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 / 5;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2

    def test_divop_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float a = 10.0 / 5.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2.0

    def test_modop_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 % 3;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_negop_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = -10;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == -10

    def test_negop_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float a = -10.0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == -10.0

    def test_bidmas(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 2 + (5 * ((0)) + 5) * 3 + 2 - (2 + (2 * 4 - 12 / 2)) / 2;
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 17

    def test_op_with_variables(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10;
                int b = 5;
                int c = a * b * a;
                int d = 10 * 5 * 10;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 500
        assert interpreter.stack_snapshots[-4].stack[-2].value == 500

    # test_addop_vector_vector
    # test_addop_int_float
    # test_addop_float_int
    # test_subop_int_float
    # test_subop_float_int
    # test_subop_vector_vector
    # test_mulop_int_float
    # test_mulop_float_int
    # test_mulop_float_vector
    # test_mulop_vector_float
    # test_divop_int_float
    # test_divop_float_int
    # test_divop_vector_float

    # endregion

    # region Logical Operator
    def test_not_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = !1;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_logical_and_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 0 && 0;
                int b = 1 && 0;
                int c = 1 && 1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-3].value == 0
        assert interpreter.stack_snapshots[-4].stack[-2].value == 0
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_logical_or_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 0 || 0;
                int b = 1 || 0;
                int c = 1 || 1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-3].value == 0
        assert interpreter.stack_snapshots[-4].stack[-2].value == 1
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    def test_logical_equals(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 == 1;
                int b = "a" == "b";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-2].value == 1
        assert interpreter.stack_snapshots[-4].stack[-1].value == 0

    def test_logical_notequals_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1 != 1;
                int b = 1 != 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-2].value == 0
        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    # endregion

    # region Relational Operator
    def test_compare_greaterthan_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 > 1;
                int b = 10 > 10;
                int c = 10 > 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_compare_greaterthanorequal_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 >= 1;
                int b = 10 >= 10;
                int c = 10 >= 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_compare_lessthan_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 < 1;
                int b = 10 < 10;
                int c = 10 < 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_compare_lessthanorequal_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 10 <= 1;
                int b = 10 <= 10;
                int c = 10 <= 20;

                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    # endregion

    # region Bitwise Operator
    def test_bitwise_or_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 5 | 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 7

    def test_bitwise_xor_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 ^ 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 5

    def test_bitwise_not_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = ~1;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == -2

    def test_bitwise_and_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 & 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 2

    def test_bitwise_shiftleft_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 << 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 28

    def test_bitwise_shiftright_op(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 7 >> 2;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.stack_snapshots[-4].stack[-1].value == 1

    # endregion

    # region Assignment
    def test_assignment(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                a = 4;

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 4

    def test_assignment_complex(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                a = a * 2 + 8;

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 10

    def test_assignment_string_constant(self):
        ncs = self.compile(
            """
            void main()
            {
                string a = "A";

                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == "A"

    def test_assignment_string_enginecall(self):
        ncs = self.compile(
            """
            void main()
            {
                string a = GetGlobalString("A");

                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("GetGlobalString", lambda identifier: identifier)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == "A"

    def test_addition_assignment_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;
                value += 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 3

    def test_addition_assignment_int_float(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;
                value += 2.0;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 3

    def test_addition_assignment_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 1.0;
                value += 2.0;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 3.0

    def test_addition_assignment_float_int(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 1.0;
                value += 2;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintFloat"
        assert snap.arg_values[0] == 3.0

    def test_addition_assignment_string_string(self):
        ncs = self.compile(
            """
            void main()
            {
                string value = "a";
                value += "b";

                PrintString(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintString"
        assert snap.arg_values[0] == "ab"

    def test_subtraction_assignment_int_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value -= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [6]

    def test_subtraction_assignment_int_float(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value -= 2.0;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values[0] == 8.0

    def test_subtraction_assignment_float_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0;
                value -= 2.0;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintFloat"
        assert snap.arg_values[0] == 8.0

    def test_subtraction_assignment_float_int(self):
        ncs = self.compile(
            """
            void main()
            {
                float value = 10.0;
                value -= 2;

                PrintFloat(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 8.0

    def test_multiplication_assignment(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 10;
                value *= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [40]

    def test_division_assignment(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 12;
                value /= 2 * 2;

                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        assert snap.function_name == "PrintInteger"
        assert snap.arg_values == [3]

    # endregion

    # region Switch Statements
    def test_switch_no_breaks(self):
        ncs = self.compile(
            """
            void main()
            {
                switch (2)
                {
                    case 1:
                        PrintInteger(1);
                    case 2:
                        PrintInteger(2);
                    case 3:
                        PrintInteger(3);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 2
        assert interpreter.action_snapshots[1].arg_values[0] == 3

    def test_switch_jump_over(self):
        ncs = self.compile(
            """
            void main()
            {
                switch (4)
                {
                    case 1:
                        PrintInteger(1);
                    case 2:
                        PrintInteger(2);
                    case 3:
                        PrintInteger(3);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 0

    def test_switch_with_breaks(self):
        ncs = self.compile(
            """
            void main()
            {
                switch (3)
                {
                    case 1:
                        PrintInteger(1);
                        break;
                    case 2:
                        PrintInteger(2);
                        break;
                    case 3:
                        PrintInteger(3);
                        break;
                    case 4:
                        PrintInteger(4);
                        break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_switch_with_default(self):
        ncs = self.compile(
            """
            void main()
            {
                switch (4)
                {
                    case 1:
                        PrintInteger(1);
                        break;
                    case 2:
                        PrintInteger(2);
                        break;
                    case 3:
                        PrintInteger(3);
                        break;
                    default:
                        PrintInteger(4);
                        break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 4

    def test_switch_scoped_blocks(self):
        ncs = self.compile(
            """
            void main()
            {
                switch (2)
                {
                    case 1:
                    {
                        int inner = 10;
                        PrintInteger(inner);
                    }
                    break;

                    case 2:
                    {
                        int inner = 20;
                        PrintInteger(inner);
                    }
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 20

    # endregion

    def test_scope(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 1;

                if (value == 1)
                {
                    value = 2;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_scoped_block(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;

                {
                    int b = 2;
                    PrintInteger(a);
                    PrintInteger(b);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    # region If/Else Conditions
    def test_if(self):
        ncs = self.compile(
            """
            void main()
            {
                if(0)
                {
                    PrintInteger(0);
                }

                if(1)
                {
                    PrintInteger(1);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_if_multiple_conditions(self):
        ncs = self.compile(
            """
            void main()
            {
                if(1 && 2 && 3)
                {
                    PrintInteger(0);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_if_else(self):
        ncs = self.compile(
            """
            void main()
            {
                if (0) {    PrintInteger(0); }
                else {      PrintInteger(1); }

                if (1) {    PrintInteger(2); }
                else {      PrintInteger(3); }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2

    def test_if_else_if(self):
        ncs = self.compile(
            """
            void main()
            {
                if (0)      { PrintInteger(0); }
                else if (0) { PrintInteger(1); }

                if (1)      { PrintInteger(2); } // hit
                else if (1) { PrintInteger(3); }

                if (1)      { PrintInteger(4); } // hit
                else if (0) { PrintInteger(5); }

                if (0)      { PrintInteger(6); }
                else if (1) { PrintInteger(7); } // hit
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 2
        assert interpreter.action_snapshots[1].arg_values[0] == 4
        assert interpreter.action_snapshots[2].arg_values[0] == 7

    def test_if_else_if_else(self):
        ncs = self.compile(
            """
            void main()
            {
                if (0)      { PrintInteger(0); }
                else if (0) { PrintInteger(1); }
                else        { PrintInteger(3); } // hit

                if (0)      { PrintInteger(4); }
                else if (1) { PrintInteger(5); } // hit
                else        { PrintInteger(6); }

                if (1)      { PrintInteger(7); } // hit
                else if (1) { PrintInteger(8); }
                else        { PrintInteger(9); }

                if (1)      { PrintInteger(10); } //hit
                else if (0) { PrintInteger(11); }
                else        { PrintInteger(12); }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 4
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 5
        assert interpreter.action_snapshots[2].arg_values[0] == 7
        assert interpreter.action_snapshots[3].arg_values[0] == 10

    def test_single_statement_if(self):
        ncs = self.compile(
            """
            void main()
            {
                if (1) PrintInteger(222);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 222

    def test_single_statement_else_if_else(self):
        ncs = self.compile(
            """
            void main()
            {
                if (0) PrintInteger(11);
                else if (0) PrintInteger(22);
                else PrintInteger(33);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 33

    # endregion

    # region While
    def test_while_loop(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_while_loop_with_break(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_while_loop_with_continue(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                    continue;
                    PrintInteger(99);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_while_loop_scope(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 11;
                int outer = 22;
                while (value)
                {
                    int inner = 33;
                    value = 0;
                    continue;
                    outer = 99;
                }

                PrintInteger(outer);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 22
        assert interpreter.action_snapshots[1].arg_values[0] == 0

    # endregion

    # region Do While
    def test_do_while_loop(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_do_while_loop_with_break(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                    break;
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 3

    def test_do_while_loop_with_continue(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                    continue;
                    PrintInteger(99);
                } while (value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 3
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 1

    def test_do_while_loop_scope(self):
        ncs = self.compile(
            """
            void main()
            {
                int outer = 11;
                int value = 22;
                do
                {
                    int inner = 33;
                    value = 0;
                } while (value);

                PrintInteger(outer);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 11
        assert interpreter.action_snapshots[1].arg_values[0] == 0

    # endregion

    # region For Loop
    def test_for_loop(self):
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 3

    def test_for_loop_with_break(self):
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_for_loop_with_continue(self):
        ncs = self.compile(
            """
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                    continue;
                    PrintInteger(99);
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 3
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2
        assert interpreter.action_snapshots[2].arg_values[0] == 3

    def test_for_loop_scope(self):
        ncs = self.compile(
            """
            void main()
            {
                int i = 11;
                int outer = 22;
                for (i = 0; i <= 5; i += 1)
                {
                    int inner = 33;
                    break;
                }

                PrintInteger(i);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    # endregion

    def test_float_notations(self):
        ncs = self.compile(
            """
            void main()
            {
                PrintFloat(1.0f);
                PrintFloat(2.0);
                PrintFloat(3f);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 3

    def test_multi_declarations(self):
        ncs = self.compile(
            """
            void main()
            {
                int value1, value2 = 1, value3 = 2;

                PrintInteger(value1);
                PrintInteger(value2);
                PrintInteger(value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 1
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_local_declarations(self):
        ncs = self.compile(
            """
            void main()
            {
                int INT;
                float FLOAT;
                string STRING;
                location LOCATION;
                effect EFFECT;
                talent TALENT;
                event EVENT;
                vector VECTOR;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_global_declarations(self):
        ncs = self.compile(
            """
            int INT;
            float FLOAT;
            string STRING;
            location LOCATION;
            effect EFFECT;
            talent TALENT;
            event EVENT;
            vector VECTOR;

            void main()
            {

            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert any(inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.SAVEBP)

    def test_global_initializations(self):
        ncs = self.compile(
            """
            int INT = 0;
            float FLOAT = 0.0;
            string STRING = "";
            vector VECTOR = [0.0, 0.0, 0.0];

            void main()
            {
                PrintInteger(INT);
                PrintFloat(FLOAT);
                PrintString(STRING);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == 0.0
        assert interpreter.action_snapshots[-1].arg_values[0] == ""
        assert any(inst for inst in ncs.instructions if inst.ins_type == NCSInstructionType.SAVEBP)

    def test_global_initialization_with_unary(self):
        ncs = self.compile(
            """
            int INT = -1;

            void main()
            {
                PrintInteger(INT);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == -1

    def test_comment(self):
        ncs = self.compile(
            """
            void main()
            {
                // int a = "abc"; // [] /*
                int a = 0;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_multiline_comment(self):
        ncs = self.compile(
            """
            void main()
            {
                /* int
                abc =
                ;; 123
                */

                string aaa = "";
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_return(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;

                if (a == 1)
                {
                    PrintInteger(a);
                    return;
                }

                PrintInteger(0);
                return;
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_return_parenthesis(self):
        ncs = self.compile(
            """
            int test()
            {
                return(321);
            }

            void main()
            {
                int value = test();
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[0].arg_values[0] == 321

    def test_return_parenthesis_constant(self):
        ncs = self.compile(
            """
            int test()
            {
                return(TRUE);
            }

            void main()
            {
                int value = test();
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[0].arg_values[0] == 1

    def test_int_parenthesis_declaration(self):
        ncs = self.compile(
            """
            void main()
            {
                int value = (123);
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 123

    def test_include_builtin(self):
        otherscript = """
            void TestFunc()
            {
                PrintInteger(123);
            }
        """.encode(encoding="windows-1252")

        ncs = self.compile(
            """
            #include "otherscript"

            void main()
            {
                TestFunc();
            }
        """,
            library={"otherscript": otherscript},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_include_lookup(self):
        includetest_script_path = Path("./tests/files").resolve()
        if not includetest_script_path.is_dir():
            import errno
            msg = "Could not find includetest.nss in the include folder!"
            raise FileNotFoundError(errno.ENOENT, msg, str(includetest_script_path))
        ncs = self.compile(
            """
            #include "includetest"

            void main()
            {
                TestFunc();
            }
        """,
            library_lookup=includetest_script_path,
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_nested_include(self):
        first_script = """
            int SOME_COST = 13;

            void TestFunc(int value)
            {
                PrintInteger(value);
            }
        """.encode(encoding="windows-1252")

        second_script = """
            #include "first_script"
        """.encode(encoding="windows-1252")

        ncs = self.compile(
            """
            #include "second_script"

            void main()
            {
                TestFunc(SOME_COST);
            }
        """,
            library={"first_script": first_script, "second_script": second_script},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 13

    def test_missing_include(self):
        source = """
            #include "otherscript"

            void main()
            {
                TestFunc();
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_global_int_addition_assignment(self):
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 2;

            void main()
            {
                int local1 = 3;
                int local2 = 4;

                global1 += local1;
                global2 = local2 + global1;

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 4
        assert interpreter.action_snapshots[-1].arg_values[0] == 8

    def test_global_int_subtraction_assignment(self):
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 10;

            void main()
            {
                int local1 = 100;
                int local2 = 1000;

                global1 -= local1;              // 1 - 100 = -99
                global2 = local2 - global1;     // 1000 - -99 = 1099

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == -99
        assert interpreter.action_snapshots[-1].arg_values[0] == 1099

    def test_global_int_multiplication_assignment(self):
        ncs = self.compile(
            """
            int global1 = 1;
            int global2 = 10;

            void main()
            {
                int local1 = 100;
                int local2 = 1000;

                global1 *= local1;              // 1 * 100 = 100
                global2 = local2 * global1;     // 1000 * 100 = 100000

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 100
        assert interpreter.action_snapshots[-1].arg_values[0] == 100000

    def test_global_int_division_assignment(self):
        ncs = self.compile(
            """
            int global1 = 1000;
            int global2 = 100;

            void main()
            {
                int local1 = 10;
                int local2 = 1;

                global1 /= local1;              // 1000 / 10 = 100
                global2 = global1 / local2;     // 100 / 1 = 100

                PrintInteger(global1);
                PrintInteger(global2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 100
        assert interpreter.action_snapshots[-1].arg_values[0] == 100

    def test_imported_global_variable(self):
        otherscript = """
            int iExperience = 55;
        """.encode(encoding="windows-1252")

        ncs = self.compile(
            """
            #include "otherscript"

            void main()
            {
                object oPlayer = GetPCSpeaker();
                GiveXPToCreature(oPlayer, iExperience);
            }
        """,
            library={"otherscript": otherscript},
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[1].arg_values[1] == 55

    def test_declaration_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a;
                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_declaration_float(self):
        ncs = self.compile(
            """
            void main()
            {
                float a;
                PrintFloat(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 0.0

    def test_declaration_string(self):
        ncs = self.compile(
            """
            void main()
            {
                string a;
                PrintString(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == ""

    def test_vector(self):
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(2.0, 4.0, 4.0);
                float mag = VectorMagnitude(vec);
                PrintFloat(mag);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.set_mock("VectorMagnitude", lambda vec: vec.magnitude())
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_vector_notation(self):
        ncs = self.compile(
            """
            void main()
            {
                vector vec = [1.0, 2.0, 3.0];
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 3.0

    def test_vector_get_components(self):
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(2.0, 4.0, 6.0);
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_vector_set_components(self):
        ncs = self.compile(
            """
            void main()
            {
                vector vec = Vector(0.0, 0.0, 0.0);
                vec.x = 2.0;
                vec.y = 4.0;
                vec.z = 6.0;
                PrintFloat(vec.x);
                PrintFloat(vec.y);
                PrintFloat(vec.z);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", Vector3)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 2.0
        assert interpreter.action_snapshots[-2].arg_values[0] == 4.0
        assert interpreter.action_snapshots[-1].arg_values[0] == 6.0

    def test_struct_get_members(self):
        ncs = self.compile(
            """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                PrintInteger(abc.value1);
                PrintString(abc.value2);
                PrintFloat(abc.value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 0
        assert interpreter.action_snapshots[-2].arg_values[0] == ""
        assert interpreter.action_snapshots[-1].arg_values[0] == 0.0

    def test_struct_get_invalid_member(self):
        source = """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                PrintFloat(abc.value4);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_struct_set_members(self):
        ncs = self.compile(
            """
            struct ABC
            {
                int value1;
                string value2;
                float value3;
            };

            void main()
            {
                struct ABC abc;
                abc.value1 = 123;
                abc.value2 = "abc";
                abc.value3 = 3.14;
                PrintInteger(abc.value1);
                PrintString(abc.value2);
                PrintFloat(abc.value3);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 123
        assert interpreter.action_snapshots[-2].arg_values[0] == "abc"
        self.assertAlmostEqual(3.14, interpreter.action_snapshots[-1].arg_values[0].value)

    def test_prefix_increment_sp_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = ++a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_prefix_increment_bp_int(self):
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = ++a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 2

    def test_postfix_increment_sp_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = a++;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_postfix_increment_bp_int(self):
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = a++;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_prefix_decrement_sp_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = --a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_prefix_decrement_bp_int(self):
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = --a;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 0

    def test_postfix_decrement_sp_int(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 1;
                int b = a--;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_postfix_decrement_bp_int(self):
        ncs = self.compile(
            """
            int a = 1;

            void main()
            {
                int b = a--;

                PrintInteger(a);
                PrintInteger(b);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-2].arg_values[0] == 0
        assert interpreter.action_snapshots[-1].arg_values[0] == 1

    def test_assignmentless_expression(self):
        ncs = self.compile(
            """
            void main()
            {
                int a = 123;

                1;
                GetCheatCode(1);
                "abc";

                PrintInteger(a);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values[0] == 123

    # region Script Subroutines
    def test_prototype_no_args(self):
        ncs = self.compile(
            """
            void test();

            void main()
            {
                test();
            }

            void test()
            {
                PrintInteger(56);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 56

    def test_prototype_with_arg(self):
        ncs = self.compile(
            """
            void test(int value);

            void main()
            {
                test(57);
            }

            void test(int value)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 57

    def test_prototype_with_three_args(self):
        ncs = self.compile(
            """
            void test(int a, int b, int c)
            {
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }

            void main()
            {
                int a = 1, b = 2, c = 3;
                test(a, b, c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-3].arg_values[0] == 1
        assert interpreter.action_snapshots[-2].arg_values[0] == 2
        assert interpreter.action_snapshots[-1].arg_values[0] == 3

    def test_prototype_with_many_args(self):
        ncs = self.compile(
            """
            void test(int a, effect z, int b, int c, int d = 4)
            {
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
                PrintInteger(d);
            }

            void main()
            {
                int a = 1, b = 2, c = 3;
                effect z;

                test(a, z, b, c);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-4].arg_values[0] == 1
        assert interpreter.action_snapshots[-3].arg_values[0] == 2
        assert interpreter.action_snapshots[-2].arg_values[0] == 3
        assert interpreter.action_snapshots[-1].arg_values[0] == 4

    def test_prototype_with_default_arg(self):
        ncs = self.compile(
            """
            void test(int value = 57);

            void main()
            {
                test();
            }

            void test(int value = 57)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 57

    def test_prototype_with_default_constant_arg(self):
        ncs = self.compile(
            """
            void test(int value = DAMAGE_TYPE_COLD);

            void main()
            {
                test();
            }

            void test(int value = DAMAGE_TYPE_COLD)
            {
                PrintInteger(value);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 32

    def test_prototype_missing_arg(self):
        source = """
            void test(int value);

            void main()
            {
                test();
            }

            void test(int value)
            {
                PrintInteger(value);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_prototype_missing_arg_and_default(self):
        source = """
            void test(int value1, int value2 = 123);

            void main()
            {
                test();
            }

            void test(int value1, int value2 = 123)
            {
                PrintInteger(value1);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_prototype_default_before_required(self):
        source = """
            void test(int value1 = 123, int value2);

            void main()
            {
                test(123, 123);
            }

            void test(int value1 = 123, int value2)
            {
                PrintInteger(value1);
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    def test_redefine_function(self):
        script = """
            void test()
            {

            }

            void test()
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_double_prototype(self):
        script = """
            void test();
            void test();
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_after_definition(self):
        script = """
            void test()
            {

            }

            void test();
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_param_mismatch(self):
        script = """
            void test(int a);

            void test()
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_default_param_mismatch(self):
        """This test is disabled for now."""
        # script = """
        #     void test(int a = 1);
        #
        #     void test(int a = 2)
        #     {
        #
        #     }
        # """
        # self.assertRaises(CompileError, self.compile, script)

    def test_prototype_and_definition_return_mismatch(self):
        script = """
            void test(int a);

            int test(int a)
            {

            }
        """
        self.assertRaises(CompileError, self.compile, script)

    def test_call_undefined(self):
        script = """
            void main()
            {
                test(0);
            }
        """

        self.assertRaises(CompileError, self.compile, script)

    def test_call_void_with_no_args(self):
        ncs = self.compile(
            """
            void test()
            {
                PrintInteger(123);
            }

            void main()
            {
                test();
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 123

    def test_call_void_with_one_arg(self):
        ncs = self.compile(
            """
            void test(int value)
            {
                PrintInteger(value);
            }

            void main()
            {
                test(123);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 123

    def test_call_void_with_two_args(self):
        ncs = self.compile(
            """
            void test(int value1, int value2)
            {
                PrintInteger(value1);
                PrintInteger(value2);
            }

            void main()
            {
                test(1, 2);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 2
        assert interpreter.action_snapshots[0].arg_values[0] == 1
        assert interpreter.action_snapshots[1].arg_values[0] == 2

    def test_call_int_with_no_args(self):
        ncs = self.compile(
            """
            int test()
            {
                return 5;
            }

            void main()
            {
                int x = test();
                PrintInteger(x);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 5

    def test_call_int_with_no_args_and_forward_declared(self):
        ncs = self.compile(
            """
            int test();

            int test()
            {
                return 5;
            }

            void main()
            {
                int x = test();
                PrintInteger(x);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert len(interpreter.action_snapshots) == 1
        assert interpreter.action_snapshots[0].arg_values[0] == 5

    def test_call_param_mismatch(self):
        source = """
            int test(int a)
            {
                return a;
            }

            void main()
            {
                test("123");
            }
        """

        self.assertRaises(CompileError, self.compile, source)

    # endregion

    def test_switch_scope_a(self):
        ncs = self.compile(
            """
            int shape;
            int harmful;

            void main()
            {
                object oTarget = OBJECT_SELF;
                effect e1, e2;
                effect e3;

                shape = SHAPE_SPHERE;

                switch (1)
                {
                    case 1:
                        harmful = FALSE;
                        e1 = EffectMovementSpeedIncrease(99);

                        if (1 == 1)
                        {
                            e1 = EffectLinkEffects(e1, EffectVisualEffect(VFX_DUR_SPEED));
                        }

                        GiveXPToCreature(OBJECT_SELF, 100);
                        GetHasSpellEffect(FORCE_POWER_SPEED_BURST, oTarget);
                    break;
                }
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()

        assert interpreter.action_snapshots[-1].arg_values == [8, 0]

    def test_switch_scope_b(self):
        ncs = self.compile(
            """
            int test(int abc)
            {
             GiveXPToCreature(GetFirstPC(), abc);
            }

            void main()
            {
                test(123);
            }
        """
        )
        ncs = self.compile(
            """
            int Cort_XP(int abc)
            {
                GiveXPToCreature(GetFirstPC(), abc);
            }

            void main() {
                int abc = 2500;
                Cort_XP(abc);
            }
        """
        )

        interpreter = Interpreter(ncs)
        interpreter.run()


if __name__ == "__main__":
    unittest.main()
