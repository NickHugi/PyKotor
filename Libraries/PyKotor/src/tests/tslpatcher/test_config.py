import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.capsule import Capsule
from pykotor.tslpatcher.patcher import ModInstaller
from utility.path import Path


class TestLookupResourceFunction(unittest.TestCase):
    def setUp(self):
        self.patch = Mock()
        self.patch.sourcefile = "test_filename"
        self.patch.sourcefolder = "."
        self.patch.saveas = "test_filename"
        self.config = ModInstaller("", "", "")
        self.config.mod_path = Path("test_mod_path")
        self.output_container_path = Path("test_output_container_path")

    def tearDown(self):
        pass

    def test_lookup_resource_replace_file_true(self):
        # Arrange
        self.patch.replace_file = True

        mock_binary_reader = MagicMock()
        mock_binary_reader.read_all.return_value = "BinaryReader read_all result"
        
        with patch("pykotor.common.stream.BinaryReader.from_auto", return_value=mock_binary_reader):

            # Act
            result = self.config.lookup_resource(self.patch, self.output_container_path)  # type: ignore[reportGeneralTypeIssues]

            # Assert
            self.assertEqual(result, "BinaryReader read_all result")

    def test_lookup_resource_capsule_exists_true(self):
        self.patch.replace_file = False

        mock_binary_reader = MagicMock()
        mock_binary_reader.read_all.return_value = "BinaryReader read_all result"
        
        capsule = Capsule("test.mod", create_nonexisting=True)
        with patch("pykotor.common.stream.BinaryReader.from_auto", return_value=mock_binary_reader):
            result = self.config.lookup_resource(
                self.patch,
                self.output_container_path,  # type: ignore[reportGeneralTypeIssues]
                True,
                capsule,
            )
            self.assertEqual(result, None)

    def test_lookup_resource_no_capsule_exists_true(self):
        # Arrange
        self.patch.replace_file = False

        mock_binary_reader = MagicMock()
        mock_binary_reader.read_all.return_value = "BinaryReader read_all result"
        
        with patch("pykotor.common.stream.BinaryReader.from_auto", return_value=mock_binary_reader):
            result = self.config.lookup_resource(
                self.patch,
                self.output_container_path,  # type: ignore[reportGeneralTypeIssues]
                True,
                None,
            )
            self.assertEqual(result, "BinaryReader read_all result")

    def test_lookup_resource_no_capsule_exists_false(self):
        # Arrange
        self.patch.replace_file = False

        mock_binary_reader = MagicMock()
        mock_binary_reader.read_all.return_value = "BinaryReader read_all result"
        
        with patch("pykotor.common.stream.BinaryReader.from_auto", return_value=mock_binary_reader):
            result = self.config.lookup_resource(
                self.patch,
                self.output_container_path,  # type: ignore[reportGeneralTypeIssues]
                False,
                None,
            )
            self.assertEqual(result, "BinaryReader read_all result")

    def test_lookup_resource_capsule_exists_false(self):
        self.patch.replace_file = False

        mock_binary_reader = MagicMock()
        mock_binary_reader.read_all.return_value = "BinaryReader read_all result"
        
        capsule = Capsule("test.mod", create_nonexisting=True)
        with patch("pykotor.common.stream.BinaryReader.from_auto", return_value=mock_binary_reader):
            result = self.config.lookup_resource(
                self.patch,
                self.output_container_path,  # type: ignore[reportGeneralTypeIssues]
                False,
                capsule,
            )
            self.assertEqual(result, "BinaryReader read_all result")

    def test_lookup_resource_replace_file_true_no_file(self):
        # Arrange
        self.patch.replace_file = True

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertIsNone(self.config.lookup_resource(self.patch, self.output_container_path))

    def test_lookup_resource_capsule_exists_true_no_file(self):
        # Arrange
        self.patch.replace_file = False
        capsule = Capsule("test.mod", create_nonexisting=True)

        with patch("pykotor.extract.capsule.Capsule.resource") as mock_resource:
            mock_resource.side_effect = FileNotFoundError

            # Act & Assert
            self.assertIsNone(
                self.config.lookup_resource(
                    self.patch,
                    self.output_container_path,
                    exists_at_output_location=True,
                    capsule=capsule,
                )
            )

    def test_lookup_resource_no_capsule_exists_true_no_file(self):
        # Arrange
        self.patch.replace_file = False

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertIsNone(
                self.config.lookup_resource(self.patch, self.output_container_path, exists_at_output_location=True, capsule=None)
            )

    def test_lookup_resource_no_capsule_exists_false_no_file(self):
        # Arrange
        self.patch.replace_file = False

        with patch("pykotor.common.stream.BinaryReader.load_file") as mock_load_file:
            mock_load_file.side_effect = FileNotFoundError

            # Act & Assert
            self.assertIsNone(
                self.config.lookup_resource(self.patch, self.output_container_path, exists_at_output_location=False, capsule=None)
            )


class TestShouldPatchFunction(unittest.TestCase):
    def setUp(self):
        self.patcher = ModInstaller("", "", "")
        self.patcher.game_path = MagicMock()
        self.patcher.game_path.name = "swkotor"
        self.patcher.log = MagicMock()

    def test_replace_file_exists_destination_dot(self):
        patch = MagicMock(name="patch", destination=".", replace_file=True, saveas="file1", sourcefile="file1", action="Patch ")
        result = self.patcher.should_patch(patch, exists=True)
        self.patcher.log.add_note.assert_called_once_with("Patching 'file1' and replacing existing file in the 'swkotor' folder")
        self.assertTrue(result)

    def test_replace_file_exists_saveas_destination_dot(self):
        patch = MagicMock(name="patch", destination=".", replace_file=True, saveas="file2", sourcefile="file1", action="Patch ")
        result = self.patcher.should_patch(patch, exists=True)
        self.patcher.log.add_note.assert_called_once_with(
            "Patching 'file1' and replacing existing file 'file2' in the 'swkotor' folder"
        )
        self.assertTrue(result)

    def test_replace_file_exists_destination_override(self):
        patch = MagicMock(
            name="patch", destination="Override", replace_file=True, saveas="file1", sourcefile="file1", action="Patch "
        )
        result = self.patcher.should_patch(patch, exists=True)
        self.patcher.log.add_note.assert_called_once_with("Patching 'file1' and replacing existing file in the 'Override' folder")
        self.assertTrue(result)

    def test_replace_file_exists_saveas_destination_override(self):
        patch = MagicMock(
            name="patch", destination="Override", replace_file=True, saveas="file2", sourcefile="file1", action="Compile"
        )
        result = self.patcher.should_patch(patch, exists=True)
        self.patcher.log.add_note.assert_called_once_with(
            "Compiling 'file1' and replacing existing file 'file2' in the 'Override' folder"
        )
        self.assertTrue(result)

    def test_replace_file_not_exists_saveas_destination_override(self):
        patch = MagicMock(
            name="patch", destination="Override", replace_file=True, saveas="file2", sourcefile="file1", action="Copy "
        )
        result = self.patcher.should_patch(patch, exists=False)
        self.patcher.log.add_note.assert_called_once_with("Copying 'file1' and saving as 'file2' in the 'Override' folder")
        self.assertTrue(result)

    def test_replace_file_not_exists_destination_override(self):
        patch = MagicMock(
            name="patch", destination="Override", replace_file=True, saveas="file1", sourcefile="file1", action="Copy "
        )
        result = self.patcher.should_patch(patch, exists=False)
        self.patcher.log.add_note.assert_called_once_with("Copying 'file1' and saving to the 'Override' folder")
        self.assertTrue(result)

    def test_replace_file_exists_destination_capsule(self):
        patch = MagicMock(
            name="patch", destination="capsule.mod", replace_file=True, saveas="file1", sourcefile="file1", action="Patch "
        )
        result = self.patcher.should_patch(patch, exists=True, capsule=True)
        self.patcher.log.add_note.assert_called_once_with(
            "Patching 'file1' and replacing existing file in the 'capsule.mod' archive"
        )
        self.assertTrue(result)

    def test_replace_file_exists_saveas_destination_capsule(self):
        patch = MagicMock(
            name="patch", destination="capsule.mod", replace_file=True, saveas="file2", sourcefile="file1", action="Patch "
        )
        result = self.patcher.should_patch(patch, exists=True, capsule=True)
        self.patcher.log.add_note.assert_called_once_with(
            "Patching 'file1' and replacing existing file 'file2' in the 'capsule.mod' archive"
        )
        self.assertTrue(result)

    def test_replace_file_not_exists_saveas_destination_capsule(self):
        patch = MagicMock(
            name="patch", destination="capsule.mod", replace_file=True, saveas="file2", sourcefile="file1", action="Copy "
        )
        result = self.patcher.should_patch(patch, exists=False, capsule=MagicMock(patch="some path"))
        self.patcher.log.add_note.assert_called_once_with("Copying 'file1' and saving as 'file2' in the 'capsule.mod' archive")
        self.assertTrue(result)

    def test_replace_file_not_exists_destination_capsule(self):
        patch = MagicMock(
            name="patch", destination="capsule.mod", replace_file=True, saveas="file1", sourcefile="file1", action="Copy "
        )
        result = self.patcher.should_patch(patch, exists=False, capsule=MagicMock(patch="some path"))
        self.patcher.log.add_note.assert_called_once_with("Copying 'file1' and adding to the 'capsule.mod' archive")
        self.assertTrue(result)

    def test_not_replace_file_exists_skip_false(self):
        patch = MagicMock(
            destination="other",
            replace_file=False,
            saveas="file3",
            sourcefile="file1",
            action="Patching",
            skip_if_not_replace=False,
        )
        result = self.patcher.should_patch(patch, exists=True)
        self.assertTrue(result)

    def test_skip_if_not_replace_not_replace_file_exists(self):
        patch = MagicMock(
            destination="other",
            replace_file=False,
            saveas="file3",
            sourcefile="file1",
            action="Patching",
            skip_if_not_replace=True,
        )
        result = self.patcher.should_patch(patch, exists=True)
        self.assertFalse(result)

    def test_capsule_not_exist(self):
        patch = MagicMock(destination="capsule", action="Patching", sourcefile="file1")
        capsule = MagicMock()
        capsule.path().exists.return_value = False
        result = self.patcher.should_patch(patch, capsule=capsule)
        self.assertFalse(result)

    def test_default_behavior(self):
        patch = MagicMock(
            destination="other",
            saveas="file3",
            sourcefile="file1",
            action="Patching",
            skip_if_not_replace=False,
            replace_file=False,
        )
        result = self.patcher.should_patch(patch, exists=False)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
