import unittest
from unittest.mock import Mock, patch
from pykotor.extract.capsule import Capsule
from pykotor.tools.path import Path
from pykotor.tslpatcher.config import ModInstaller

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.patch = Mock()
        setattr(self.patch, "sourcefile", "test_filename")
        setattr(self.patch, "saveas", "test_filename")
        self.config = ModInstaller("","","")
        setattr(self.config, "mod_path", Path("test_mod_path"))
        self.output_container_path = Path("test_output_container_path")

    def tearDown(self):
        pass

    def test_lookup_resource_replace_file_true(self):
        # Arrange
        setattr(self.patch, "replace_file", True)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.return_value = "BinaryReader.load_file result"

            # Act
            result = self.config.lookup_resource(self.patch, self.output_container_path)  # type: ignore[reportGeneralTypeIssues]

            # Assert
            self.assertEqual(result, "BinaryReader.load_file result")

    def test_lookup_resource_capsule_exists_true(self):
        self._do_capsule_test(
            "pykotor.extract.capsule.Capsule.resource",
            "capsule.resource result",
            True,
        )

    def test_lookup_resource_no_capsule_exists_true(self):
        # Arrange
        setattr(self.patch, "replace_file", False)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            self._do_main_test("BinaryReader.load_file result", mock_load_file, True, None)

    def test_lookup_resource_no_capsule_exists_false(self):
        # Arrange
        setattr(self.patch, "replace_file", False)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            self._do_main_test("BinaryReader.load_file result", mock_load_file, False, None)

    def test_lookup_resource_capsule_exists_false(self):
        self._do_capsule_test(
            "pykotor.common.stream.BinaryReader.load_file",
            "BinaryReader.load_file result",
            False,
        )

    def _do_capsule_test(self, arg0, arg1, arg2):
        setattr(self.patch, "replace_file", False)
        capsule = Capsule("test.mod")
        with patch(arg0) as mock_resource:
            self._do_main_test(arg1, mock_resource, arg2, capsule)

    def _do_main_test(self, arg0, arg1, exists_at_output_location, capsule):
        arg1.return_value = arg0
        result = self.config.lookup_resource(
            self.patch,
            self.output_container_path,  # type: ignore[reportGeneralTypeIssues]
            exists_at_output_location,
            capsule,
        )
        self.assertEqual(result, arg0)

    def test_lookup_resource_replace_file_true_no_file(self):
        # Arrange
        setattr(self.patch, "replace_file", True)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertRaises(FileNotFoundError, self.config.lookup_resource, self.patch, self.output_container_path)

    def test_lookup_resource_capsule_exists_true_no_file(self):
        # Arrange
        setattr(self.patch, "replace_file", False)
        capsule = Capsule("test.mod")

        with patch("pykotor.extract.capsule.Capsule.resource") as mock_resource:
            mock_resource.side_effect = FileNotFoundError

            # Act & Assert
            self.assertRaises(FileNotFoundError, self.config.lookup_resource, self.patch, self.output_container_path, exists_at_output_location=True, capsule=capsule)

    def test_lookup_resource_no_capsule_exists_true_no_file(self):
        # Arrange
        setattr(self.patch, "replace_file", False)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertRaises(FileNotFoundError, self.config.lookup_resource, self.patch, self.output_container_path, exists_at_output_location=True, capsule=None)

    def test_lookup_resource_no_capsule_exists_false_no_file(self):
        # Arrange
        setattr(self.patch, "replace_file", False)

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertRaises(FileNotFoundError, self.config.lookup_resource, self.patch, self.output_container_path, exists_at_output_location=False, capsule=None)

if __name__ == "__main__":
    unittest.main()