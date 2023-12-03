import pathlib
import sys
import unittest
from unittest import TestCase

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.common.geometry import Vector3
from pykotor.common.script import DataType
from pykotor.resource.formats.ncs.compiler.interpreter import Stack


class TestStack(TestCase):
    def test_peek_past_vector(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1.0)  # -20
        stack.add(DataType.VECTOR, Vector3(2.0, 3.0, 4.0))  # -16
        stack.add(DataType.FLOAT, 5.0)  # -4
        print(stack.peek(-20))

    def test_move_negative(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.move(-12)
        snapshop = stack.state()
        self.assertEqual(3, len(snapshop))
        self.assertEqual(3.0, snapshop.pop())
        self.assertEqual(2.0, snapshop.pop())
        self.assertEqual(1.0, snapshop.pop())

    def test_move_zero(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.move(0)
        snapshop = stack.state()
        self.assertEqual(6, len(snapshop))
        self.assertEqual(6.0, snapshop.pop())
        self.assertEqual(5.0, snapshop.pop())
        self.assertEqual(4.0, snapshop.pop())
        self.assertEqual(3.0, snapshop.pop())
        self.assertEqual(2.0, snapshop.pop())
        self.assertEqual(1.0, snapshop.pop())

    def test_copy_down_single(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.copy_down(-12, 4)

        self.assertEqual(6, stack.peek(-12))

    def test_copy_down_many(self):
        stack = Stack()
        stack.add(DataType.FLOAT, 1)  # -24
        stack.add(DataType.FLOAT, 2)  # -20
        stack.add(DataType.FLOAT, 3)  # -16
        stack.add(DataType.FLOAT, 4)  # -12
        stack.add(DataType.FLOAT, 5)  # -8
        stack.add(DataType.FLOAT, 6)  # -4

        stack.copy_down(-24, 12)
        print(stack.state())

        self.assertEqual(4, stack.peek(-24))
        self.assertEqual(5, stack.peek(-20))
        self.assertEqual(6, stack.peek(-16))


if __name__ == "__main__":
    unittest.main()
