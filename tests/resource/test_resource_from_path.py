import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType


class TestResourceIdentifier(unittest.TestCase):
    """ This test was created because of the many soft, hard-to-find errors that would happen if this function ever fails."""
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
            # Edge cases
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
            {
                "return_type": "invalid",
                "file_path": "",
                "expected_resname": "",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/invalid.ext",
                "expected_resname": "invalid",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/.hidden",
                "expected_resname": ".hidden",
                "expected_restype": ResourceType.INVALID,
            },
            {
                "return_type": "invalid",
                "file_path": "C:/path/to/invalid.",
                "expected_resname": "invalid",
                "expected_restype": ResourceType.INVALID,
            },
            # Error cases
            {
                "return_type": "error",
                "file_path": None,
                "expected_resname": None,
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
            if return_type == "error":
                self.assertRaises((ValueError, TypeError), ResourceIdentifier.from_path, file_path)
                continue
            else:
                result = ResourceIdentifier.from_path(file_path)

            # Assert
            self.assertEqual(result.resname, expected_resname)
            self.assertEqual(result.restype, expected_restype)


if __name__ == "__main__":
    unittest.main()
