from unittest import TestCase

from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.interpreter import Interpreter
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.optimizers import RemoveNopOptimizer


class TestNCSOptimizers(TestCase):

    def compile(self, script: str) -> NCS:
        nssLexer = NssLexer()
        nssParser = NssParser()
        lex = nssLexer.lexer
        parser = nssParser.parser

        t = parser.parse(script, tracking=True)

        ncs = NCS()
        t.compile(ncs,,
        return ncs

    def test_no_op_optimizer(self):
        ncs = self.compile("""
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
        """)

        ncs.optimize([RemoveNopOptimizer()])
        ncs.print()

        interpreter = Interpreter(ncs)
        interpreter.run()

        self.assertEqual(3, len(interpreter.action_snapshots))
        self.assertEqual(3, interpreter.action_snapshots[0].arg_values[0])
        self.assertEqual(2, interpreter.action_snapshots[1].arg_values[0])
        self.assertEqual(1, interpreter.action_snapshots[2].arg_values[0])
