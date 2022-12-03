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
                object oSomething = GetObjectByTag("something", 15);
            }
        """)

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(1, len(interpreter.action_snapshots))

        self.assertEqual("GetObjectByTag", interpreter.action_snapshots[0].function_name)
        self.assertEqual(["something", 15], interpreter.action_snapshots[0].arg_values)
