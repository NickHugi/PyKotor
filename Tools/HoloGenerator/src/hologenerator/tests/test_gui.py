"""
Unit tests for HoloGenerator GUI functionality.
Only runs when tkinter is available.
"""

import unittest
import sys
from unittest.mock import Mock, patch, MagicMock

# Test if GUI is available
try:
    from hologenerator.gui import GUI_AVAILABLE
    if GUI_AVAILABLE:
        import tkinter as tk
        from hologenerator.gui.main import HoloGeneratorGUI
except ImportError:
    GUI_AVAILABLE = False


@unittest.skipUnless(GUI_AVAILABLE, "GUI not available (tkinter not installed)")
class TestHoloGeneratorGUI(unittest.TestCase):
    """Test cases for the HoloGeneratorGUI class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_gui_initialization(self):
        """Test GUI initialization."""
        gui = HoloGeneratorGUI(self.root)
        
        # Check that basic components exist
        self.assertIsNotNone(gui.path1_var)
        self.assertIsNotNone(gui.path2_var)
        self.assertIsNotNone(gui.output_var)
        self.assertIsNotNone(gui.file_mode_var)
        self.assertIsNotNone(gui.generator)
        
        # Check default values
        self.assertEqual(gui.output_var.get(), "changes.ini")
        self.assertFalse(gui.file_mode_var.get())
    
    def test_validate_inputs_empty_paths(self):
        """Test input validation with empty paths."""
        gui = HoloGeneratorGUI(self.root)
        
        # Mock messagebox to avoid actual dialogs
        with patch('hologenerator.gui.main.messagebox') as mock_messagebox:
            result = gui.validate_inputs()
            
            self.assertFalse(result)
            mock_messagebox.showerror.assert_called()
    
    @patch('hologenerator.gui.main.Path')
    def test_validate_inputs_invalid_installation(self, mock_path):
        """Test input validation with invalid KOTOR installation."""
        gui = HoloGeneratorGUI(self.root)
        
        # Set up mock paths
        mock_path1 = Mock()
        mock_path1.exists.return_value = True
        mock_path1.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=False)))
        
        mock_path2 = Mock()
        mock_path2.exists.return_value = True
        mock_path2.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=False)))
        
        mock_path.return_value = mock_path1
        mock_path.side_effect = [mock_path1, mock_path2]
        
        # Set paths
        gui.path1_var.set("/fake/path1")
        gui.path2_var.set("/fake/path2")
        gui.output_var.set("changes.ini")
        gui.file_mode_var.set(False)  # Installation mode
        
        # Mock messagebox to avoid actual dialogs
        with patch('hologenerator.gui.main.messagebox') as mock_messagebox:
            result = gui.validate_inputs()
            
            self.assertFalse(result)
            mock_messagebox.showerror.assert_called()
    
    @patch('hologenerator.gui.main.Path')
    def test_validate_inputs_valid_installation(self, mock_path):
        """Test input validation with valid KOTOR installation."""
        gui = HoloGeneratorGUI(self.root)
        
        # Set up mock paths with chitin.key
        mock_chitin = Mock()
        mock_chitin.exists.return_value = True
        
        mock_path1 = Mock()
        mock_path1.exists.return_value = True
        mock_path1.__truediv__ = Mock(return_value=mock_chitin)
        
        mock_path2 = Mock()
        mock_path2.exists.return_value = True
        mock_path2.__truediv__ = Mock(return_value=mock_chitin)
        
        mock_path.side_effect = [mock_path1, mock_path2]
        
        # Set paths
        gui.path1_var.set("/fake/kotor1")
        gui.path2_var.set("/fake/kotor2")
        gui.output_var.set("changes.ini")
        gui.file_mode_var.set(False)  # Installation mode
        
        result = gui.validate_inputs()
        self.assertTrue(result)
    
    @patch('hologenerator.gui.main.Path')
    def test_validate_inputs_file_mode(self, mock_path):
        """Test input validation in file mode."""
        gui = HoloGeneratorGUI(self.root)
        
        # Set up mock paths
        mock_path1 = Mock()
        mock_path1.exists.return_value = True
        
        mock_path2 = Mock()
        mock_path2.exists.return_value = True
        
        mock_path.side_effect = [mock_path1, mock_path2]
        
        # Set paths and file mode
        gui.path1_var.set("/fake/file1.txt")
        gui.path2_var.set("/fake/file2.txt")
        gui.output_var.set("changes.ini")
        gui.file_mode_var.set(True)  # File mode
        
        result = gui.validate_inputs()
        self.assertTrue(result)
    
    @patch('hologenerator.gui.main.readFileAsText')
    def test_file_upload_handling(self, mock_read_file):
        """Test file upload handling."""
        gui = HoloGeneratorGUI(self.root)
        
        # Mock file reading
        mock_read_file.return_value = "Test file content"
        
        # Create a mock file object
        mock_file = Mock()
        mock_file.name = "test.txt"
        
        # Mock event with file
        mock_event = Mock()
        mock_event.target.files = [mock_file]
        
        # This would be more complex to test due to the async nature
        # and the need to mock FileReader API
        # For now, just test that the method exists
        self.assertTrue(hasattr(gui, '_generate_config_thread'))
    
    def test_log_message(self):
        """Test log message functionality."""
        gui = HoloGeneratorGUI(self.root)
        
        # Test logging a message
        test_message = "Test log message"
        gui.log_message(test_message)
        
        # Check that the message was added to the text widget
        content = gui.output_text.get(1.0, tk.END)
        self.assertIn(test_message, content)
    
    def test_clear_output(self):
        """Test clearing output functionality."""
        gui = HoloGeneratorGUI(self.root)
        
        # Add some content
        gui.log_message("Test message")
        
        # Clear it
        gui.clear_output()
        
        # Check that content is cleared
        content = gui.output_text.get(1.0, tk.END).strip()
        self.assertEqual(content, "")
    
    @patch('hologenerator.gui.main.filedialog')
    def test_browse_path1_installation_mode(self, mock_filedialog):
        """Test browsing for path1 in installation mode."""
        gui = HoloGeneratorGUI(self.root)
        gui.file_mode_var.set(False)  # Installation mode
        
        # Mock directory selection
        mock_filedialog.askdirectory.return_value = "/selected/path"
        
        gui.browse_path1()
        
        # Check that askdirectory was called and path was set
        mock_filedialog.askdirectory.assert_called_once()
        self.assertEqual(gui.path1_var.get(), "/selected/path")
    
    @patch('hologenerator.gui.main.filedialog')
    def test_browse_path1_file_mode(self, mock_filedialog):
        """Test browsing for path1 in file mode."""
        gui = HoloGeneratorGUI(self.root)
        gui.file_mode_var.set(True)  # File mode
        
        # Mock file selection
        mock_filedialog.askopenfilename.return_value = "/selected/file.txt"
        
        gui.browse_path1()
        
        # Check that askopenfilename was called and path was set
        mock_filedialog.askopenfilename.assert_called_once()
        self.assertEqual(gui.path1_var.get(), "/selected/file.txt")
    
    @patch('hologenerator.gui.main.filedialog')
    def test_browse_output(self, mock_filedialog):
        """Test browsing for output file."""
        gui = HoloGeneratorGUI(self.root)
        
        # Mock file save dialog
        mock_filedialog.asksaveasfilename.return_value = "/output/changes.ini"
        
        gui.browse_output()
        
        # Check that asksaveasfilename was called and path was set
        mock_filedialog.asksaveasfilename.assert_called_once()
        self.assertEqual(gui.output_var.get(), "/output/changes.ini")
    
    @patch('hologenerator.gui.main.messagebox')
    def test_show_about(self, mock_messagebox):
        """Test showing about dialog."""
        gui = HoloGeneratorGUI(self.root)
        
        gui.show_about()
        
        # Check that showinfo was called
        mock_messagebox.showinfo.assert_called_once()
        args, kwargs = mock_messagebox.showinfo.call_args
        self.assertEqual(args[0], "About HoloGenerator")
        self.assertIn("HoloGenerator", args[1])


@unittest.skipUnless(GUI_AVAILABLE, "GUI not available (tkinter not installed)")
class TestGUIMain(unittest.TestCase):
    """Test cases for GUI main function."""
    
    @patch('hologenerator.gui.main.tk.Tk')
    @patch('hologenerator.gui.main.ttk.Style')
    def test_main_function(self, mock_style, mock_tk):
        """Test the main GUI function."""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        mock_style_instance = Mock()
        mock_style.return_value = mock_style_instance
        
        # Mock the application
        with patch('hologenerator.gui.main.HoloGeneratorGUI') as mock_gui:
            # Import and call main
            from hologenerator.gui.main import main
            
            # Mock mainloop to prevent hanging
            mock_root.mainloop = Mock()
            
            main()
            
            # Verify initialization
            mock_tk.assert_called_once()
            mock_style.assert_called_once()
            mock_gui.assert_called_once_with(mock_root)


class TestGUIImports(unittest.TestCase):
    """Test GUI import protection."""
    
    def test_gui_available_flag(self):
        """Test that GUI_AVAILABLE flag is properly set."""
        try:
            import tkinter
            expected = True
        except ImportError:
            expected = False
        
        from hologenerator.gui import GUI_AVAILABLE
        self.assertEqual(GUI_AVAILABLE, expected)
    
    @patch('hologenerator.gui.main.TKINTER_AVAILABLE', False)
    def test_gui_without_tkinter(self):
        """Test GUI behavior when tkinter is not available."""
        with patch('hologenerator.gui.main.tk', None):
            from hologenerator.gui.main import HoloGeneratorGUI
            
            # Should raise ImportError when tkinter is not available
            with self.assertRaises(ImportError):
                mock_root = Mock()
                HoloGeneratorGUI(mock_root)
    
    def test_main_without_tkinter(self):
        """Test main function when tkinter is not available."""
        with patch('hologenerator.gui.main.TKINTER_AVAILABLE', False):
            from hologenerator.gui.main import main
            
            # Should exit with error code when tkinter not available
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)