"""
Unit tests for the HoloGenerator core functionality.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from hologenerator.core.differ import KotorDiffer, DiffResult, FileChange
from hologenerator.core.changes_ini import ChangesIniGenerator
from hologenerator.core.generator import ConfigurationGenerator


class TestKotorDiffer(unittest.TestCase):
    """Test cases for the KotorDiffer class."""
    
    def setUp(self):
        self.differ = KotorDiffer()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test KotorDiffer initialization."""
        self.assertIsInstance(self.differ.gff_types, set)
        self.assertGreater(len(self.differ.gff_types), 0)
    
    def test_is_kotor_install_valid(self):
        """Test valid KOTOR installation detection."""
        # Create a mock KOTOR installation
        kotor_dir = self.temp_path / "kotor"
        kotor_dir.mkdir()
        (kotor_dir / "chitin.key").touch()
        
        self.assertTrue(self.differ._is_kotor_install(kotor_dir))
    
    def test_is_kotor_install_invalid(self):
        """Test invalid KOTOR installation detection."""
        # Directory without chitin.key
        invalid_dir = self.temp_path / "invalid"
        invalid_dir.mkdir()
        
        self.assertFalse(self.differ._is_kotor_install(invalid_dir))
    
    def test_get_resource_type(self):
        """Test resource type detection."""
        self.assertEqual(self.differ._get_resource_type("test.gff"), "gff")
        self.assertEqual(self.differ._get_resource_type("test.2da"), "2da")
        self.assertEqual(self.differ._get_resource_type("test.TLK"), "tlk")
        self.assertEqual(self.differ._get_resource_type(Path("test.SSF")), "ssf")
    
    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        test_file = self.temp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        hash1 = self.differ._calculate_file_hash(test_file)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA256 hash length
        
        # Same file should produce same hash
        hash2 = self.differ._calculate_file_hash(test_file)
        self.assertEqual(hash1, hash2)
    
    def test_2da_to_text_conversion(self):
        """Test 2DA to text conversion."""
        # Mock 2DA object
        mock_2da = Mock()
        mock_2da.columns = ["Column1", "Column2"]
        mock_2da.rows = [
            {"Column1": "Value1", "Column2": "Value2"},
            {"Column1": "Value3", "Column2": "Value4"}
        ]
        
        text = self.differ._2da_to_text(mock_2da)
        
        self.assertIn("2DA V2.b", text)
        self.assertIn("Column1", text)
        self.assertIn("Value1", text)
        self.assertIn("\t", text)  # Tab separated
    
    def test_tlk_to_text_conversion(self):
        """Test TLK to text conversion."""
        # Mock TLK object
        mock_tlk = Mock()
        mock_tlk.language = "English"
        
        # Mock entries
        mock_entry1 = Mock()
        mock_entry1.text = "Hello World"
        mock_entry1.voiceover = "hello.wav"
        mock_entry1.sound_length = 1.5
        
        mock_entry2 = Mock()
        mock_entry2.text = ""
        mock_entry2.voiceover = ""
        mock_entry2.sound_length = 0
        
        mock_tlk.entries = [mock_entry1, mock_entry2]
        
        text = self.differ._tlk_to_text(mock_tlk)
        
        self.assertIn("TLK Language: English", text)
        self.assertIn("Entry 0:", text)
        self.assertIn("Hello World", text)
        self.assertIn("hello.wav", text)
        # Empty entry should not appear
        self.assertNotIn("Entry 1:", text)
    
    def test_diff_installations_invalid_paths(self):
        """Test diff_installations with invalid paths."""
        invalid_path = self.temp_path / "nonexistent"
        
        result = self.differ.diff_installations(invalid_path, invalid_path)
        
        self.assertIsInstance(result, DiffResult)
        self.assertEqual(len(result.errors), 2)  # Both paths should error
        self.assertEqual(len(result.changes), 0)


class TestChangesIniGenerator(unittest.TestCase):
    """Test cases for the ChangesIniGenerator class."""
    
    def setUp(self):
        self.generator = ChangesIniGenerator()
    
    def test_init(self):
        """Test ChangesIniGenerator initialization."""
        self.assertIsInstance(self.generator.gff_extensions, set)
        self.assertGreater(len(self.generator.gff_extensions), 0)
    
    def test_generate_empty_diff(self):
        """Test generating config from empty diff result."""
        diff_result = DiffResult()
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[Settings]", config)
        self.assertIn("WindowCaption=Generated Mod Configuration", config)
    
    def test_generate_with_added_file(self):
        """Test generating config with added files."""
        diff_result = DiffResult()
        change = FileChange("Override/test.txt", "added", "txt")
        diff_result.add_change(change)
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[InstallList]", config)
        self.assertIn("[Override]", config)
        self.assertIn("File1=Override", config)
        self.assertIn("File1=test.txt", config)
    
    def test_generate_with_gff_modification(self):
        """Test generating config with GFF modifications."""
        diff_result = DiffResult()
        change = FileChange("test.utc", "modified", "utc")
        change.diff_lines = ["+ SomeField: NewValue", "- SomeField: OldValue"]
        diff_result.add_change(change)
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[GFFList]", config)
        self.assertIn("File1=test.utc", config)
        self.assertIn("[test.utc]", config)
    
    def test_generate_with_2da_modification(self):
        """Test generating config with 2DA modifications."""
        diff_result = DiffResult()
        change = FileChange("test.2da", "modified", "2da")
        change.diff_lines = ["+ 1\tValue1\tValue2", "- 1\tOldValue1\tOldValue2"]
        diff_result.add_change(change)
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[2DAList]", config)
        self.assertIn("File1=test.2da", config)
        self.assertIn("[test.2da]", config)
    
    def test_process_tlk_change(self):
        """Test processing TLK file changes."""
        diff_result = DiffResult()
        change = FileChange("dialog.tlk", "modified", "tlk")
        change.diff_lines = ["+ Entry 42: Hello World", "+ Entry 100: Goodbye"]
        diff_result.add_change(change)
        
        config = self.generator.generate_from_diff(diff_result)
        
        self.assertIn("[TLKList]", config)
        self.assertIn("StrRef42=Modified", config)
        self.assertIn("StrRef100=Modified", config)


class TestGFFPatcher(unittest.TestCase):
    """Test cases for the GFFPatcher helper class."""
    
    def test_determine_field_type_bool(self):
        """Test field type determination for boolean values."""
        from hologenerator.core.changes_ini import GFFPatcher
        
        self.assertEqual(GFFPatcher._determine_field_type(True), "UINT8")
        self.assertEqual(GFFPatcher._determine_field_type(False), "UINT8")
    
    def test_determine_field_type_int(self):
        """Test field type determination for integer values."""
        from hologenerator.core.changes_ini import GFFPatcher
        
        self.assertEqual(GFFPatcher._determine_field_type(100), "INT16")
        self.assertEqual(GFFPatcher._determine_field_type(65000), "UINT16")
        self.assertEqual(GFFPatcher._determine_field_type(100000), "INT32")
        self.assertEqual(GFFPatcher._determine_field_type(5000000000), "UINT32")
    
    def test_determine_field_type_float(self):
        """Test field type determination for float values."""
        from hologenerator.core.changes_ini import GFFPatcher
        
        self.assertEqual(GFFPatcher._determine_field_type(3.14), "FLOAT")
        self.assertEqual(GFFPatcher._determine_field_type(0.0), "FLOAT")
    
    def test_determine_field_type_string(self):
        """Test field type determination for string values."""
        from hologenerator.core.changes_ini import GFFPatcher
        
        self.assertEqual(GFFPatcher._determine_field_type("hello"), "EXOSTRING")
        self.assertEqual(GFFPatcher._determine_field_type(""), "EXOSTRING")
    
    def test_generate_field_patch(self):
        """Test field patch generation."""
        from hologenerator.core.changes_ini import GFFPatcher
        
        patch = GFFPatcher.generate_field_patch("SomeField", "old", "new")
        
        self.assertEqual(patch["FieldPath"], "SomeField")
        self.assertEqual(patch["FieldType"], "EXOSTRING")
        self.assertEqual(patch["Value"], "new")


class TestTwoDAPatcher(unittest.TestCase):
    """Test cases for the TwoDAPatcher helper class."""
    
    def test_generate_row_patch(self):
        """Test row patch generation."""
        from hologenerator.core.changes_ini import TwoDAPatcher
        
        patch = TwoDAPatcher.generate_row_patch(5, "Name", "OldName", "NewName")
        
        self.assertEqual(patch["RowIndex"], "5")
        self.assertEqual(patch["ColumnLabel"], "Name")
        self.assertEqual(patch["Value"], "NewName")
    
    def test_generate_add_row_patch(self):
        """Test add row patch generation."""
        from hologenerator.core.changes_ini import TwoDAPatcher
        
        row_data = {
            "RowLabel": "NewRow",
            "Column1": "Value1",
            "Column2": "Value2"
        }
        patch = TwoDAPatcher.generate_add_row_patch(row_data)
        
        self.assertEqual(patch["RowLabel"], "NewRow")
        self.assertEqual(patch["Col_Column1"], "Value1")
        self.assertEqual(patch["Col_Column2"], "Value2")


class TestConfigurationGenerator(unittest.TestCase):
    """Test cases for the ConfigurationGenerator class."""
    
    def setUp(self):
        self.generator = ConfigurationGenerator()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test ConfigurationGenerator initialization."""
        self.assertIsNotNone(self.generator.differ)
        self.assertIsNotNone(self.generator.generator)
    
    @patch('hologenerator.core.generator.KotorDiffer')
    @patch('hologenerator.core.generator.ChangesIniGenerator')
    def test_generate_config(self, mock_ini_gen, mock_differ):
        """Test configuration generation."""
        # Mock the differ to return a simple diff result
        mock_diff_result = DiffResult()
        mock_change = FileChange("test.txt", "added", "txt")
        mock_diff_result.add_change(mock_change)
        
        mock_differ_instance = mock_differ.return_value
        mock_differ_instance.diff_installations.return_value = mock_diff_result
        
        # Mock the generator to return a simple config
        mock_ini_gen_instance = mock_ini_gen.return_value
        mock_ini_gen_instance.generate_from_diff.return_value = "[Settings]\nTest=Value\n"
        
        # Create test paths
        path1 = self.temp_path / "kotor1"
        path2 = self.temp_path / "kotor2"
        output_path = self.temp_path / "changes.ini"
        
        # Generate config
        result = self.generator.generate_config(path1, path2, output_path)
        
        # Verify calls were made
        mock_differ_instance.diff_installations.assert_called_once_with(path1, path2)
        mock_ini_gen_instance.generate_from_diff.assert_called_once_with(mock_diff_result)
        
        # Verify result
        self.assertEqual(result, "[Settings]\nTest=Value\n")
        
        # Verify file was written
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text(encoding='utf-8'), "[Settings]\nTest=Value\n")
    
    @patch('hologenerator.core.generator.KotorDiffer')
    def test_generate_from_files(self, mock_differ):
        """Test configuration generation from individual files."""
        # Mock the differ to return a file change
        mock_change = FileChange("test.txt", "modified", "txt")
        
        mock_differ_instance = mock_differ.return_value
        mock_differ_instance.diff_files.return_value = mock_change
        
        # Create test files
        file1 = self.temp_path / "file1.txt"
        file2 = self.temp_path / "file2.txt"
        file1.write_text("original content")
        file2.write_text("modified content")
        
        # Generate config
        result = self.generator.generate_from_files(file1, file2)
        
        # Verify the differ was called
        mock_differ_instance.diff_files.assert_called_once_with(file1, file2)
        
        # Should return non-empty result when there are changes
        self.assertIsInstance(result, str)
    
    @patch('hologenerator.core.generator.KotorDiffer')
    def test_generate_from_files_no_changes(self, mock_differ):
        """Test configuration generation from identical files."""
        # Mock the differ to return None (no changes)
        mock_differ_instance = mock_differ.return_value
        mock_differ_instance.diff_files.return_value = None
        
        # Create test files
        file1 = self.temp_path / "file1.txt"
        file2 = self.temp_path / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")
        
        # Generate config
        result = self.generator.generate_from_files(file1, file2)
        
        # Should return empty string when no changes
        self.assertEqual(result, "")


class TestDiffResult(unittest.TestCase):
    """Test cases for the DiffResult class."""
    
    def setUp(self):
        self.diff_result = DiffResult()
    
    def test_init(self):
        """Test DiffResult initialization."""
        self.assertEqual(len(self.diff_result.changes), 0)
        self.assertEqual(len(self.diff_result.errors), 0)
    
    def test_add_change(self):
        """Test adding changes to diff result."""
        change = FileChange("test.txt", "added", "txt")
        self.diff_result.add_change(change)
        
        self.assertEqual(len(self.diff_result.changes), 1)
        self.assertEqual(self.diff_result.changes[0], change)
    
    def test_add_error(self):
        """Test adding errors to diff result."""
        error_msg = "Test error message"
        self.diff_result.add_error(error_msg)
        
        self.assertEqual(len(self.diff_result.errors), 1)
        self.assertEqual(self.diff_result.errors[0], error_msg)
    
    def test_get_changes_by_type(self):
        """Test filtering changes by type."""
        change1 = FileChange("test1.txt", "added", "txt")
        change2 = FileChange("test2.txt", "modified", "txt")
        change3 = FileChange("test3.txt", "added", "txt")
        
        self.diff_result.add_change(change1)
        self.diff_result.add_change(change2)
        self.diff_result.add_change(change3)
        
        added_changes = self.diff_result.get_changes_by_type("added")
        modified_changes = self.diff_result.get_changes_by_type("modified")
        
        self.assertEqual(len(added_changes), 2)
        self.assertEqual(len(modified_changes), 1)
        self.assertEqual(modified_changes[0], change2)
    
    def test_get_changes_by_resource_type(self):
        """Test filtering changes by resource type."""
        change1 = FileChange("test1.txt", "added", "txt")
        change2 = FileChange("test2.gff", "modified", "gff")
        change3 = FileChange("test3.txt", "added", "txt")
        
        self.diff_result.add_change(change1)
        self.diff_result.add_change(change2)
        self.diff_result.add_change(change3)
        
        txt_changes = self.diff_result.get_changes_by_resource_type("txt")
        gff_changes = self.diff_result.get_changes_by_resource_type("gff")
        
        self.assertEqual(len(txt_changes), 2)
        self.assertEqual(len(gff_changes), 1)
        self.assertEqual(gff_changes[0], change2)


class TestFileChange(unittest.TestCase):
    """Test cases for the FileChange class."""
    
    def test_init(self):
        """Test FileChange initialization."""
        change = FileChange("test.txt", "added", "txt")
        
        self.assertEqual(change.path, "test.txt")
        self.assertEqual(change.change_type, "added")
        self.assertEqual(change.resource_type, "txt")
        self.assertIsNone(change.old_content)
        self.assertIsNone(change.new_content)
        self.assertEqual(change.diff_lines, [])
    
    def test_init_with_content(self):
        """Test FileChange initialization with content."""
        diff_lines = ["+ New line", "- Old line"]
        change = FileChange(
            "test.txt", 
            "modified", 
            "txt", 
            "old content", 
            "new content", 
            diff_lines
        )
        
        self.assertEqual(change.old_content, "old content")
        self.assertEqual(change.new_content, "new content")
        self.assertEqual(change.diff_lines, diff_lines)


if __name__ == '__main__':
    unittest.main()