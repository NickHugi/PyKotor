from unittest import TestCase

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter, ActionSnapshot
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser


class TestNSSCompiler(TestCase):
    def compile(self, script: str) -> NCS:
        nssLexer = NssLexer()
        nssParser = NssParser()
        lex = nssLexer.lexer
        parser = nssParser.parser

        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs)
        return ncs

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

    # region Arithmetic Tests
    def test_addop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10 + 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(15, interpreter.stack_snapshots[-2][0].value)

    def test_addop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0 + 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(15.0, interpreter.stack_snapshots[-2][0].value)

    def test_addop_string_string(self):
        ncs = self.compile("""
            void main()
            {
                string value = "abc" + "def";
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual("abcdef", interpreter.stack_snapshots[-2][0].value)

    def test_subop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int value = 10 - 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(5, interpreter.stack_snapshots[-2][0].value)

    def test_subop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float value = 10.0 - 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(5.0, interpreter.stack_snapshots[-2][0].value)

    def test_mulop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 * 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(50, interpreter.stack_snapshots[-2][0].value)

    def test_mulop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float a = 10.0 * 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(50.0, interpreter.stack_snapshots[-2][0].value)

    def test_divop_int_int(self):
        ncs = self.compile("""
            void main()
            {
                int a = 10 / 5;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2, interpreter.stack_snapshots[-2][0].value)

    def test_divop_float_float(self):
        ncs = self.compile("""
            void main()
            {
                float a = 10.0 / 5.0;
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(2.0, interpreter.stack_snapshots[-2][0].value)

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
