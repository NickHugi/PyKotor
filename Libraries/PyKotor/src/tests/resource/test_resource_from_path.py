import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src").resolve()
if PYKOTOR_PATH.exists():
    working_dir = str(PYKOTOR_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
        os.chdir(PYKOTOR_PATH.parent)
    sys.path.insert(0, working_dir)
if UTILITY_PATH.exists():
    working_dir = str(UTILITY_PATH)
    if working_dir in sys.path:
        sys.path.remove(working_dir)
    sys.path.insert(0, working_dir)

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType

class TestResourceType(unittest.TestCase):
    def test_from_invalid(self):
        invalid = ResourceType.from_invalid(extension="aSdF")
        self.assertEqual(invalid, ResourceType.INVALID)
        self.assertEqual(invalid.type_id, ResourceType.INVALID.type_id)
        self.assertEqual(invalid.contents, ResourceType.INVALID.contents)
        self.assertEqual(invalid.category, ResourceType.INVALID.category)
        self.assertEqual(invalid.extension, "asdf")
        self.assertEqual(repr(invalid), "ResourceType.INVALID_aSdF")
        self.assertEqual(repr(ResourceType.INVALID), "ResourceType.INVALID")
        self.assertEqual(str(invalid), "ASDF")
        self.assertNotEqual(invalid.extension, ResourceType.INVALID.extension)
    def test_from_extension(self):
        acquired_type = ResourceType.from_extension("tlk")
        self.assertEqual(acquired_type, ResourceType.TLK)
        self.assertEqual("tLK", ResourceType.TLK)
        self.assertEqual("Tlk", acquired_type)
        self.assertEqual(ResourceType.TLK.extension, "tlk")
        self.assertEqual(ResourceType.TLK.type_id, 2018)
        self.assertEqual(repr(ResourceType.TLK), "ResourceType.TLK")
        self.assertEqual(str(ResourceType.TLK), "TLK")
        self.assertEqual(ResourceType.TLK.contents, "binary")
        self.assertEqual(ResourceType.TLK.category, "Talk Tables")
        self.assertEqual(acquired_type.extension, "tlk")
        self.assertEqual(acquired_type.type_id, 2018)
        self.assertEqual(acquired_type.contents, "binary")
        self.assertEqual(acquired_type.category, "Talk Tables")

class TestResourceIdentifier(unittest.TestCase):
    """ These tests were created because of the many soft, hard-to-find errors that occur all over when this function ever fails."""
    def test_from_path(self):
        test_cases = [
            # Happy path tests
            {
                "return_type": "ResourceType",
                "file_path": "C:/path/to/resource.mdl",
                "expected_resname": "resource",
                "expected_restype": ResourceType.MDL,
            },
            {
                "return_type": "ResourceType",
                "file_path": "C:/path/to/texture.tGa",
                "expected_resname": "texture",
                "expected_restype": ResourceType.TGA,
            },
            {
                "return_type": "ResourceType",
                "file_path": "C:/path/to/SounD.wav",
                "expected_resname": "SounD",
                "expected_restype": ResourceType.WAV,
            },
            {
                "return_type": "ResourceType",
                "file_path": "C:/path/to/asdf.Tlk.XmL",
                "expected_resname": "asdf",
                "expected_restype": ResourceType.TLK_XML,
            },
            {
                "return_type": "ResourceType",
                "file_path": "C:/path/to/asdf.xyz.qwerty.gff.xml",
                "expected_resname": "asdf.xyz.qwerty",
                "expected_restype": ResourceType.GFF_XML,
            },
            # Edge cases
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/.hidden",
                "expected_resname": ".hidden",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/no_extension",
                "expected_resname": "no_extension",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/long_extension.xyz",
                "expected_resname": "long_extension",
                "expected_restype": ResourceType.INVALID,
            },
            # Error cases?
            {
                "return_type": "invalid",
                "file_path": None,
                "expected_resname": "",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "",
                "expected_resname": "",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/invalid.",
                "expected_resname": "invalid.",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/invalid.ext",
                "expected_resname": "invalid",
                "expected_restype": ResourceType.INVALID,
            },
        ]

        for test_case in test_cases:
            # Arrange
            file_path = test_case["file_path"]
            expected_resname = test_case["expected_resname"]
            expected_restype = test_case["expected_restype"]
            return_type = test_case["return_type"]

            # Act
            result = ResourceIdentifier.from_path(file_path)

            # Assert
            fail_message = f"\nresname: '{result.resname}' restype: '{result.restype}'\nexpected resname: '{expected_resname}' expected restype: '{expected_restype}'"
            self.assertEqual(result.resname, expected_resname, fail_message)
            self.assertEqual(result.restype, expected_restype, fail_message)
            if return_type == "invalid":
                self.assertRaises((ValueError, TypeError), ResourceIdentifier.validate, ResourceIdentifier.from_path(file_path))


if __name__ == "__main__":
    unittest.main()
