import unittest
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType
from pykotor.tools.path import CaseAwarePath, PurePath


class TestResourceIdentifier(unittest.TestCase):
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
                "return_type": "error",
                "file_path": "C:/path/to/long_extension.xyz",
                "expected_resname": "long_extension",
                "expected_restype": ResourceType.INVALID,
            },
            # Error cases
            {
                "return_type": "error",
                "file_path": None,
                "expected_resname": None,
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
                "return_type": "error",
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
            if return_type == "error":
                self.assertRaises((ValueError, TypeError), ResourceIdentifier.from_path, file_path)
                continue
            else:
                result = ResourceIdentifier.from_path(file_path)

            # Assert
            self.assertEqual(result.resname, expected_resname)
            self.assertEqual(result.restype, expected_restype)
