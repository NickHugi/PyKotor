from typing import Dict
from unittest import TestCase

from pykotor.common.geometry import Vector3
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import CompileException
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter, ActionSnapshot
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser


class TestNSSCompiler(TestCase):

    def compile(self, script: str, library: Dict[str, str] = None) -> NCS:
        nssLexer = NssLexer()
        nssParser = NssParser()
        nssParser.library = library
        parser = nssParser.parser

        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs

    # region Engine Call
    def test_enginecall(self):
        ncs = self.compile("""
            void main()
            {
                object oExisting = GetExitingObject();
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))

        self.assertEqual("GetExitingObject", interpreter.action_snapshots[0].function_name)
        self.assertEqual([], interpreter.action_snapshots[0].arg_values)

    def test_enginecall_return_value(self):
        ncs = self.compile("""
            void main()
            {
                int inescapable = GetAreaUnescapable();
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.set_mock("GetAreaUnescapable", lambda: 10)
        interpreter.run()

        self.assertEqual(10, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_enginecall_with_params(self):
        ncs = self.compile("""
            void main()
            {
                string tag = "something";
                int n = 15;
                object oSomething = GetObjectByTag(tag, n);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))

        self.assertEqual("GetObjectByTag", interpreter.action_snapshots[0].function_name)
        self.assertEqual(["something", 15], interpreter.action_snapshots[0].arg_values)

    def test_enginecall_with_default_params(self):
        ncs = self.compile("""
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag(tag);
            }
        """)

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

        self.assertRaises(CompileException, self.compile, script)

    def test_enginecall_with_too_many_params(self):
        script = """
            void main()
            {
                string tag = "something";
                object oSomething = GetObjectByTag("", 0, "shouldnotbehere");
            }
        """

        self.assertRaises(CompileException, self.compile, script)

    def test_enginecall_delay_command_1(self):
        ncs = self.compile("""
            void main()
            {
                object oFirstPlayer = GetFirstPC();
                DelayCommand(1.0, GiveXPToCreature(oFirstPlayer, 9001));
            }
        """)
    # endregion

    # region Operators
    def test_addop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10 + 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(15, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_addop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0 + 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(15.0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_addop_string_string(self):
        ncs = self.compile("""
            void main()
            {
                string value = "abc" + "def";
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual("abcdef", interpreter.stack_snapshots[-4].stack[-1].value)

    def test_subop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10 - 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(5, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_subop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0 - 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(5.0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_mulop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 * 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(50, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_mulop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float a = 10.0 * 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(50.0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_divop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 / 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_divop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float a = 10.0 / 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2.0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_modop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 % 3;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_negop_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = -10;
                PrintInteger(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(-10, interpreter.action_snapshots[0].arg_values[0])

    def test_negop_float(self):
        ncs = self.compile("""
            void main()
            {
                float a = -10.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(-10.0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bidmas(self):
        ncs = self.compile("""
            void main()
            {
                int value = 2 + (5 * ((0)) + 5) * 3 + 2 - (2 + (2 * 4 - 12 / 2)) / 2;
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(17, interpreter.action_snapshots[0].arg_values[0])

    def test_op_with_variables(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10;
                int b = 5;
                int c = a * b * a;
                int d = 10 * 5 * 10;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(500, interpreter.stack_snapshots[-4].stack[-1].value)
        self.assertEqual(500, interpreter.stack_snapshots[-4].stack[-2].value)

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
        ncs = self.compile("""
            void main()
            {
                int a = !1;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_logical_and_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 0 && 0;
                int b = 1 && 0;
                int c = 1 && 1;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-3].value)
        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-2].value)
        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_logical_or_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 0 || 0;
                int b = 1 || 0;
                int c = 1 || 1;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-3].value)
        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-2].value)
        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_logical_equals_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 1 == 1;
                int b = 1 == 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-2].value)
        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_logical_notequals_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 1 != 1;
                int b = 1 != 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.stack_snapshots[-4].stack[-2].value)
        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-1].value)
    # endregion

    # region Relational Operator
    def test_compare_greaterthan_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 > 1;
                int b = 10 > 10;
                int c = 10 > 20;
                
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, interpreter.action_snapshots[-3].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[-2].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[-1].arg_values[0])

    def test_compare_greaterthanorequal_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 >= 1;
                int b = 10 >= 10;
                int c = 10 >= 20;
                
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, interpreter.action_snapshots[-3].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[-2].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[-1].arg_values[0])

    def test_compare_lessthan_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 < 1;
                int b = 10 < 10;
                int c = 10 < 20;
                
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.action_snapshots[-3].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[-2].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[-1].arg_values[0])

    def test_compare_lessthanorequal_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 <= 1;
                int b = 10 <= 10;
                int c = 10 <= 20;
                
                PrintInteger(a);
                PrintInteger(b);
                PrintInteger(c);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.action_snapshots[-3].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[-2].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[-1].arg_values[0])

    # endregion

    # region Bitwise Operator
    def test_bitwise_or_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 5 | 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(7, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bitwise_xor_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 7 ^ 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(5, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bitwise_not_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = ~1;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(-2, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bitwise_and_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 7 & 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()
        
        self.assertEqual(2, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bitwise_shiftleft_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 7 << 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(28, interpreter.stack_snapshots[-4].stack[-1].value)

    def test_bitwise_shiftright_op(self):
        ncs = self.compile("""
            void main()
            {
                int a = 7 >> 2;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, interpreter.stack_snapshots[-4].stack[-1].value)
    # endregion

    # region Assignment
    def test_assignment(self):
        ncs = self.compile("""
            void main()
            {
                int a = 1;
                a = 4;
                
                PrintInteger(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(4, interpreter.action_snapshots[0].arg_values[0])

    def test_assignment_complex(self):
        ncs = self.compile("""
            void main()
            {
                int a = 1;
                a = a * 2 + 8;
                
                PrintInteger(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(10, interpreter.action_snapshots[0].arg_values[0])

    def test_addition_assignment_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 1;
                value += 2;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual(3, snap.arg_values[0])

    def test_addition_assignment_int_float(self):
        ncs = self.compile("""
            void main()
            {
                int value = 1;
                value += 2.0;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual(3, snap.arg_values[0])

    def test_addition_assignment_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 1.0;
                value += 2.0;
                
                PrintFloat(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintFloat", snap.function_name)
        self.assertEqual(3.0, snap.arg_values[0])

    def test_addition_assignment_float_int(self):
        ncs = self.compile("""
            void main()
            {
                float value = 1.0;
                value += 2;
                
                PrintFloat(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintFloat", snap.function_name)
        self.assertEqual(3.0, snap.arg_values[0])

    def test_addition_assignment_string_string(self):
        ncs = self.compile("""
            void main()
            {
                string value = "a";
                value += "b";
                
                PrintString(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintString", snap.function_name)
        self.assertEqual("ab", snap.arg_values[0])

    def test_subtraction_assignment_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10;
                value -= 2 * 2;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual([6], snap.arg_values)

    def test_subtraction_assignment_int_float(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10;
                value -= 2.0;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual(8.0, snap.arg_values[0])

    def test_subtraction_assignment_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0;
                value -= 2.0;
                
                PrintFloat(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintFloat", snap.function_name)
        self.assertEqual(8.0, snap.arg_values[0])

    def test_subtraction_assignment_float_int(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0;
                value -= 2;
                
                PrintFloat(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintFloat", snap.function_name)
        self.assertEqual(8.0, snap.arg_values[0])

    def test_multiplication_assignment(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10;
                value *= 2 * 2;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual([40], snap.arg_values)

    def test_division_assignment(self):
        ncs = self.compile("""
            void main()
            {
                int value = 12;
                value /= 2 * 2;
                
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        snap = interpreter.action_snapshots[-1]
        self.assertEqual("PrintInteger", snap.function_name)
        self.assertEqual([3], snap.arg_values)
    # endregion

    # region Switch Statements
    def test_switch_no_breaks(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(2, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(3, interpreter.action_snapshots[1].arg_values[0])

    def test_switch_jump_over(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, len(interpreter.action_snapshots))

    def test_switch_with_breaks(self):
        ncs = self.compile("""
            void main()
            {
                switch (2)
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
                }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(2, interpreter.action_snapshots[0].arg_values[0])

    def test_switch_with_default(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(4, interpreter.action_snapshots[0].arg_values[0])
    # endregion

    def test_scope(self):
        ncs = self.compile("""
            void main()
            {
                int value = 1;
                
                if (value == 1)
                {
                    value = 2;
                }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

    # region If/Else Conditions
    def test_if(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])

    def test_if_else(self):
        ncs = self.compile("""
            void main()
            {
                if (0) {    PrintInteger(0); }
                else {      PrintInteger(1); }
                
                if (1) {    PrintInteger(2); }
                else {      PrintInteger(3); }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])

    def test_if_else_if(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(2, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(4, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(7, interpreter.action_snapshots[2].arg_values[0])

    def test_if_else_if_else(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(4, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(5, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(7, interpreter.action_snapshots[2].arg_values[0])
        self.assertEqual(10, interpreter.action_snapshots[3].arg_values[0])
    # endregion

    # region While
    def test_while_loop(self):
        ncs = self.compile("""
            void main()
            {
                int value = 3;
                while (value)
                {
                    PrintInteger(value);
                    value -= 1;
                }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])

    def test_while_loop_with_break(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])

    def test_while_loop_with_continue(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])

    def test_while_loop_scope(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(22, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[1].arg_values[0])
    # endregion

    # region Do While
    def test_do_while_loop(self):
        ncs = self.compile("""
            void main()
            {
                int value = 3;
                do
                {
                    PrintInteger(value);
                    value -= 1;
                } while (value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])

    def test_do_while_loop_with_break(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])

    def test_do_while_loop_with_continue(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])

    def test_do_while_loop_scope(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(11, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(0, interpreter.action_snapshots[1].arg_values[0])
    # endregion

    # region For Loop
    def test_for_loop(self):
        ncs = self.compile("""
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(3, interpreter.action_snapshots[2].arg_values[0])

    def test_for_loop_with_break(self):
        ncs = self.compile("""
            void main()
            {
                int i = 99;
                for (i = 1; i <= 3; i += 1)
                {
                    PrintInteger(i);
                    break;
                }
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])

    def test_for_loop_with_continue(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(3, interpreter.action_snapshots[2].arg_values[0])

    def test_for_loop_scope(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(0, interpreter.action_snapshots[0].arg_values[0])
    # endregion

    def test_comment(self):
        ncs = self.compile("""
            void main()
            {
                // int a = "abc"; // [] /*
                int a = 0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_multiline_comment(self):
        ncs = self.compile("""
            void main()
            {
                /* int 
                abc = 
                ;; 123
                */
                
                string aaa = "";
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_return(self):
        ncs = self.compile("""
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
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])

    def test_include(self):
        otherscript = """
            void TestFunc()
            {
                PrintInteger(123);
            }
        """

        ncs = self.compile("""
            #include "otherscript"
        
            void main()
            {
                TestFunc();
            }
        """, library={"otherscript": otherscript})

        interpreter = Interpreter(ncs)
        interpreter.run()

    def test_nested_include(self):
        first_script = """
            int SOME_COST = 13;
        
            void TestFunc(int value)
            {
                PrintInteger(value);
            }
        """

        second_script = """
            #include "first_script"
        """

        ncs = self.compile("""
            #include "second_script"
        
            void main()
            {
                TestFunc(SOME_COST);
            }
        """, library={"first_script": first_script, "second_script": second_script})

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(13, interpreter.action_snapshots[0].arg_values[0])

    def test_global_variable(self):
        ncs = self.compile("""
            int value1 = 1;
            int value2 = 2;

            void main()
            {
                object oPlayer = GetPCSpeaker();
                GiveXPToCreature(oPlayer, value1);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[1].arg_values[1])

    def test_imported_global_variable(self):
        otherscript = """
            int iExperience = 55;
        """

        ncs = self.compile("""
            #include "otherscript"

            void main()
            {
                object oPlayer = GetPCSpeaker();
                GiveXPToCreature(oPlayer, iExperience);
            }
        """, library={"otherscript": otherscript})

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(55, interpreter.action_snapshots[1].arg_values[1])

    def test_declaration_int(self):
        ncs = self.compile("""
            void main()
            {
                int a;
                PrintInteger(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0, interpreter.action_snapshots[-1].arg_values[0])

    def test_declaration_float(self):
        ncs = self.compile("""
            void main()
            {
                float a;
                PrintFloat(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(0.0, interpreter.action_snapshots[-1].arg_values[0])

    def test_declaration_string(self):
        ncs = self.compile("""
            void main()
            {
                string a;
                PrintString(a);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual("", interpreter.action_snapshots[-1].arg_values[0])

    def test_vector(self):
        ncs = self.compile("""
            void main()
            {
                vector vec = Vector(2.0, 4.0, 4.0);
                float mag = VectorMagnitude(vec);
                PrintFloat(mag);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", lambda x, y, z: Vector3(x, y, z))
        interpreter.set_mock("VectorMagnitude", lambda vec: vec.magnitude())
        interpreter.run()

        self.assertEqual(6.0, interpreter.action_snapshots[-1].arg_values[0])

    def test_struct(self):
        ncs = self.compile("""
            struct ABC
            {
                int a;
            };
        
            void main()
            {
            
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.set_mock("Vector", lambda x, y, z: Vector3(x, y, z))
        interpreter.set_mock("VectorMagnitude", lambda vec: vec.magnitude())
        interpreter.run()

        #self.assertEqual(6.0, interpreter.action_snapshots[-1].arg_values[0])

    # region User-defined Functions
    def test_prototype_no_args(self):
        ncs = self.compile("""
            void test();

            void main()
            {
                test();
            }

            void test()
            {
                PrintInteger(56);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(56, interpreter.action_snapshots[0].arg_values[0])

    def test_prototype_with_args(self):
        ncs = self.compile("""
            void test(int value);

            void main()
            {
                test(57);
            }

            void test(int value)
            {
                PrintInteger(value);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(57, interpreter.action_snapshots[0].arg_values[0])

    def test_redefine_function(self):
        script = """
            void test()
            {
                
            }
        
            void test()
            {
                
            }
        """
        self.assertRaises(CompileException, self.compile, script)

    def test_double_prototype(self):
        script = """
            void test();
            void test();
        """
        self.assertRaises(CompileException, self.compile, script)

    def test_prototype_after_definition(self):
        script = """
            void test()
            {
                
            }
        
            void test();
        """
        self.assertRaises(CompileException, self.compile, script)

    def test_prototype_and_definition_param_mismatch(self):
        script = """
            void test(int a);
            
            void test()
            {
                
            }
        """
        self.assertRaises(CompileException, self.compile, script)

    def test_prototype_and_definition_return_mismatch(self):
        script = """
            void test(int a);
            
            int test(int a)
            {
                
            }
        """
        self.assertRaises(CompileException, self.compile, script)

    def test_call_undefined(self):
        script = """
            void main()
            {
                test(0);
            }
        """

        self.assertRaises(CompileException, self.compile, script)

    def test_call_void_with_no_args(self):
        ncs = self.compile("""
            void test()
            {
                PrintInteger(123);
            }
        
            void main()
            {
                test();
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(123, interpreter.action_snapshots[0].arg_values[0])

    def test_call_void_with_one_arg(self):
        ncs = self.compile("""
            void test(int value)
            {
                PrintInteger(value);
            }

            void main()
            {
                test(123);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(123, interpreter.action_snapshots[0].arg_values[0])

    def test_call_void_with_two_args(self):
        ncs = self.compile("""
            void test(int value1, int value2)
            {
                PrintInteger(value1);
                PrintInteger(value2);
            }

            void main()
            {
                test(1, 2);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, len(interpreter.action_snapshots))
        self.assertEqual(1, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])

    def test_call_int_with_no_args(self):
        ncs = self.compile("""
            int test()
            {
                return 5;
            }

            void main()
            {
                int x = test();
                PrintInteger(x);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))
        self.assertEqual(5, interpreter.action_snapshots[0].arg_values[0])
    # endregion
