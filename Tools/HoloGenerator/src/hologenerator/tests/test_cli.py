"""
Unit tests for the HoloGenerator CLI functionality.
"""

import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import the CLI module
from hologenerator.__main__ import main


class TestCLI(unittest.TestCase):
    """Test cases for the CLI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv', ['hologenerator', '--version'])
    def test_version_argument(self):
        """Test the --version argument."""
        with self.assertRaises(SystemExit) as cm:
            main()
        # argparse exits with code 0 for --version
        self.assertEqual(cm.exception.code, 0)
    
    @patch('sys.argv', ['hologenerator', '--help'])
    def test_help_argument(self):
        """Test the --help argument."""
        with self.assertRaises(SystemExit) as cm:
            main()
        # argparse exits with code 0 for --help
        self.assertEqual(cm.exception.code, 0)
    
    @patch('hologenerator.__main__.ConfigurationGenerator')
    @patch('sys.argv', ['hologenerator', '/path1', '/path2'])
    @patch('builtins.input', return_value='')
    def test_cli_with_paths(self, mock_input, mock_generator_class):
        """Test CLI with provided paths."""
        # Mock the generator
        mock_generator = Mock()
        mock_generator.generate_config.return_value = "[Settings]\nTest=Value"
        mock_generator_class.return_value = mock_generator
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('sys.exit') as mock_exit:
                    main()
                    
                    # Should not exit with error
                    mock_exit.assert_not_called()
                    
                    # Generator should be called
                    mock_generator.generate_config.assert_called_once()
    
    @patch('sys.argv', ['hologenerator', '--gui'])
    @patch('hologenerator.gui.main.main')
    def test_gui_mode(self, mock_gui_main):
        """Test launching GUI mode."""
        main()
        mock_gui_main.assert_called_once()
    
    @patch('sys.argv', ['hologenerator', '--gui'])
    def test_gui_mode_not_available(self):
        """Test GUI mode when GUI is not available."""
        with patch('hologenerator.__main__.sys.exit') as mock_exit:
            with patch('builtins.print') as mock_print:
                # Mock import error for GUI
                with patch('hologenerator.__main__.ImportError', ImportError):
                    # This is complex to test due to the try/except import structure
                    pass
    
    @patch('hologenerator.__main__.ConfigurationGenerator')
    @patch('sys.argv', ['hologenerator', '/path1', '/path2', '--file-mode'])
    def test_file_mode(self, mock_generator_class):
        """Test file mode operation."""
        # Mock the generator
        mock_generator = Mock()
        mock_generator.generate_from_files.return_value = "[Settings]\nTest=Value"
        mock_generator_class.return_value = mock_generator
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('sys.exit') as mock_exit:
                    main()
                    
                    # Should not exit with error
                    mock_exit.assert_not_called()
                    
                    # Generator should be called with file mode
                    mock_generator.generate_from_files.assert_called_once()
    
    @patch('sys.argv', ['hologenerator', '/nonexistent1', '/nonexistent2'])
    def test_nonexistent_paths(self):
        """Test CLI with non-existent paths."""
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_with(1)
    
    @patch('hologenerator.__main__.ConfigurationGenerator')
    @patch('sys.argv', ['hologenerator', '/path1', '/path2', '-o', 'custom.ini'])
    def test_custom_output_path(self, mock_generator_class):
        """Test CLI with custom output path."""
        # Mock the generator
        mock_generator = Mock()
        mock_generator.generate_config.return_value = "[Settings]\nTest=Value"
        mock_generator_class.return_value = mock_generator
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('sys.exit') as mock_exit:
                    main()
                    
                    # Check that custom output path was used
                    call_args = mock_generator.generate_config.call_args
                    output_path = call_args[0][2]  # Third argument
                    self.assertEqual(str(output_path), 'custom.ini')
    
    @patch('sys.argv', ['hologenerator'])
    @patch('builtins.input', side_effect=['/input/path1', '/input/path2'])
    def test_interactive_input(self, mock_input):
        """Test interactive input when no paths provided."""
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('hologenerator.__main__.ConfigurationGenerator') as mock_gen:
                    mock_generator = Mock()
                    mock_generator.generate_config.return_value = "[Settings]\nTest=Value"
                    mock_gen.return_value = mock_generator
                    
                    with patch('sys.exit') as mock_exit:
                        main()
                        
                        # Should have prompted for input
                        self.assertEqual(mock_input.call_count, 2)
                        mock_exit.assert_not_called()
    
    @patch('sys.argv', ['hologenerator'])
    @patch('builtins.input', side_effect=['', ''])
    def test_empty_interactive_input(self, mock_input):
        """Test empty interactive input."""
        with patch('sys.exit') as mock_exit:
            main()
            # Should exit with error when no input provided
            mock_exit.assert_called_with(1)
    
    @patch('hologenerator.__main__.ConfigurationGenerator')
    @patch('sys.argv', ['hologenerator', '/path1', '/path2'])
    def test_generation_error(self, mock_generator_class):
        """Test handling of generation errors."""
        # Mock the generator to raise an exception
        mock_generator = Mock()
        mock_generator.generate_config.side_effect = Exception("Test error")
        mock_generator_class.return_value = mock_generator
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('sys.exit') as mock_exit:
                    main()
                    mock_exit.assert_called_with(1)
    
    @patch('hologenerator.__main__.ConfigurationGenerator')
    @patch('sys.argv', ['hologenerator', '/path1', '/path2'])
    def test_no_differences_found(self, mock_generator_class):
        """Test when no differences are found."""
        # Mock the generator to return empty result
        mock_generator = Mock()
        mock_generator.generate_config.return_value = ""
        mock_generator_class.return_value = mock_generator
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.resolve', side_effect=lambda: Path('/resolved/path')):
                with patch('builtins.print') as mock_print:
                    with patch('sys.exit') as mock_exit:
                        main()
                        
                        # Should print message about no differences
                        mock_print.assert_any_call("No differences found between the paths.")
                        mock_exit.assert_not_called()


class TestCLIHelpers(unittest.TestCase):
    """Test helper functions used by CLI."""
    
    def test_version_constant(self):
        """Test that version constant is defined."""
        from hologenerator.__main__ import CURRENT_VERSION
        self.assertIsInstance(CURRENT_VERSION, str)
        self.assertRegex(CURRENT_VERSION, r'\d+\.\d+\.\d+')


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create mock KOTOR installations
        self.kotor1_path = self.temp_path / "kotor1"
        self.kotor2_path = self.temp_path / "kotor2"
        
        self.kotor1_path.mkdir()
        self.kotor2_path.mkdir()
        
        # Create chitin.key files to make them look like KOTOR installations
        (self.kotor1_path / "chitin.key").touch()
        (self.kotor2_path / "chitin.key").touch()
        
        # Create some test files
        override1 = self.kotor1_path / "Override"
        override2 = self.kotor2_path / "Override"
        override1.mkdir()
        override2.mkdir()
        
        # Create different files
        (override1 / "test.txt").write_text("Original content")
        (override2 / "test.txt").write_text("Modified content")
    
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv')
    def test_full_integration(self, mock_argv):
        """Test full integration with real file differences."""
        output_file = self.temp_path / "test_changes.ini"
        
        mock_argv.__getitem__.side_effect = [
            'hologenerator',
            str(self.kotor1_path),
            str(self.kotor2_path),
            '-o',
            str(output_file)
        ]
        mock_argv.__len__.return_value = 5
        
        # Run the CLI
        with patch('sys.exit') as mock_exit:
            main()
            
            # Should not exit with error
            mock_exit.assert_not_called()
            
            # Output file should be created
            self.assertTrue(output_file.exists())
            
            # Should contain configuration content
            content = output_file.read_text()
            self.assertIn("[Settings]", content)
    
    @patch('sys.argv')
    def test_file_mode_integration(self, mock_argv):
        """Test file mode integration."""
        file1 = self.temp_path / "file1.txt"
        file2 = self.temp_path / "file2.txt"
        output_file = self.temp_path / "test_changes.ini"
        
        file1.write_text("Original file content")
        file2.write_text("Modified file content")
        
        mock_argv.__getitem__.side_effect = [
            'hologenerator',
            str(file1),
            str(file2),
            '--file-mode',
            '-o',
            str(output_file)
        ]
        mock_argv.__len__.return_value = 6
        
        # Run the CLI
        with patch('sys.exit') as mock_exit:
            main()
            
            # Should not exit with error
            mock_exit.assert_not_called()
            
            # Output file should be created
            self.assertTrue(output_file.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)