"""
HoloGenerator GUI Interface

Tkinter-based graphical interface for the configuration generator.
All tkinter imports are protected with try-catch blocks.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING

# Protected tkinter imports
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    scrolledtext = None

# Add the PyKotor library to the path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = Path(__file__).parents[5] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)

if TYPE_CHECKING and TKINTER_AVAILABLE:
    from tkinter import Event

if TKINTER_AVAILABLE:
    from hologenerator.core.generator import ConfigurationGenerator


class HoloGeneratorGUI:
    """Main GUI application for the HoloGenerator."""
    
    def __init__(self, root: tk.Tk):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter is not available")
            
        self.root = root
        self.root.title("HoloGenerator - KOTOR Configuration Generator")
        self.root.geometry("900x700")
        
        # Variables for paths
        self.path1_var = tk.StringVar()
        self.path2_var = tk.StringVar()
        self.output_var = tk.StringVar(value="changes.ini")
        self.file_mode_var = tk.BooleanVar()
        
        # Configuration generator
        self.generator = ConfigurationGenerator()
        
        # Create the UI
        self.create_widgets()
        
        # Center the window
        self.center_window()
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="HoloGenerator", 
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle_label = ttk.Label(
            main_frame, 
            text="KOTOR Configuration Generator for HoloPatcher", 
            font=("Arial", 12)
        )
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        # Description
        desc_text = (
            "Generate changes.ini files for HoloPatcher by comparing KOTOR installations or individual files.\n"
            "Select the original and modified paths, then click Generate to create the configuration."
        )
        desc_label = ttk.Label(main_frame, text=desc_text, justify=tk.CENTER)
        desc_label.grid(row=2, column=0, columnspan=3, pady=(0, 20))
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Comparison Mode", padding="5")
        mode_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Radiobutton(
            mode_frame, 
            text="Installation Mode (compare full KOTOR installations)",
            variable=self.file_mode_var,
            value=False
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="File Mode (compare individual files)",
            variable=self.file_mode_var,
            value=True
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Path 1 selection
        ttk.Label(main_frame, text="Original Path:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.path1_var, width=60).grid(
            row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_path1).grid(
            row=4, column=2, padx=5, pady=5
        )
        
        # Path 2 selection
        ttk.Label(main_frame, text="Modified Path:").grid(
            row=5, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.path2_var, width=60).grid(
            row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_path2).grid(
            row=5, column=2, padx=5, pady=5
        )
        
        # Output file selection
        ttk.Label(main_frame, text="Output changes.ini:").grid(
            row=6, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.output_var, width=60).grid(
            row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(
            row=6, column=2, padx=5, pady=5
        )
        
        # Generate button
        self.generate_button = ttk.Button(
            main_frame, 
            text="Generate Configuration", 
            command=self.generate_config,
            style="Accent.TButton"
        )
        self.generate_button.grid(row=7, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, 
            mode='indeterminate', 
            length=500
        )
        self.progress.grid(row=8, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=9, column=0, columnspan=3, pady=5)
        
        # Output text area
        output_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        output_frame.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(10, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=15, 
            width=80,
            wrap=tk.WORD
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Save Output", command=self.save_output).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="About", command=self.show_about).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(
            side=tk.RIGHT, padx=5
        )
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def browse_path1(self):
        """Browse for the first path."""
        if self.file_mode_var.get():
            path = filedialog.askopenfilename(
                title="Select Original File",
                initialdir=self.path1_var.get() or "/"
            )
        else:
            path = filedialog.askdirectory(
                title="Select Original KOTOR Installation Directory",
                initialdir=self.path1_var.get() or "/"
            )
        if path:
            self.path1_var.set(path)
    
    def browse_path2(self):
        """Browse for the second path."""
        if self.file_mode_var.get():
            path = filedialog.askopenfilename(
                title="Select Modified File",
                initialdir=self.path2_var.get() or "/"
            )
        else:
            path = filedialog.askdirectory(
                title="Select Modified KOTOR Installation Directory", 
                initialdir=self.path2_var.get() or "/"
            )
        if path:
            self.path2_var.set(path)
    
    def browse_output(self):
        """Browse for the output file path."""
        path = filedialog.asksaveasfilename(
            title="Save changes.ini file as",
            defaultextension=".ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")],
            initialfile=self.output_var.get()
        )
        if path:
            self.output_var.set(path)
    
    def validate_inputs(self) -> bool:
        """Validate user inputs before generation."""
        path1 = Path(self.path1_var.get().strip())
        path2 = Path(self.path2_var.get().strip())
        output = self.output_var.get().strip()
        
        if not path1 or not path1.exists():
            messagebox.showerror(
                "Invalid Path", 
                "Please select a valid original path."
            )
            return False
        
        if not path2 or not path2.exists():
            messagebox.showerror(
                "Invalid Path",
                "Please select a valid modified path."
            )
            return False
        
        # Validate installation mode
        if not self.file_mode_var.get():
            if not (path1 / "chitin.key").exists():
                messagebox.showerror(
                    "Invalid KOTOR Installation",
                    f"The original path '{path1}' does not appear to be a valid KOTOR installation.\n"
                    "chitin.key file not found."
                )
                return False
            
            if not (path2 / "chitin.key").exists():
                messagebox.showerror(
                    "Invalid KOTOR Installation", 
                    f"The modified path '{path2}' does not appear to be a valid KOTOR installation.\n"
                    "chitin.key file not found."
                )
                return False
        
        if not output:
            messagebox.showerror(
                "Invalid Output Path",
                "Please specify an output file path."
            )
            return False
        
        return True
    
    def generate_config(self):
        """Generate the configuration file."""
        if not self.validate_inputs():
            return
        
        # Disable the generate button and start progress
        self.generate_button.config(state='disabled')
        self.progress.start()
        self.status_var.set("Generating configuration...")
        self.clear_output()
        
        # Run generation in a separate thread
        thread = threading.Thread(target=self._generate_config_thread)
        thread.daemon = True
        thread.start()
    
    def _generate_config_thread(self):
        """Thread function for configuration generation."""
        try:
            path1 = Path(self.path1_var.get().strip())
            path2 = Path(self.path2_var.get().strip())
            output_path = Path(self.output_var.get().strip())
            
            self.log_message(f"Starting comparison:")
            self.log_message(f"  Original: {path1}")
            self.log_message(f"  Modified: {path2}")
            self.log_message(f"  Mode: {'File comparison' if self.file_mode_var.get() else 'Installation comparison'}")
            self.log_message("")
            
            # Generate the configuration
            if self.file_mode_var.get():
                result = self.generator.generate_from_files(path1, path2)
            else:
                result = self.generator.generate_config(path1, path2, output_path)
            
            # Update UI in main thread
            self.root.after(0, self._generation_complete, result, output_path)
            
        except Exception as e:
            # Handle errors in main thread
            self.root.after(0, self._generation_error, str(e))
    
    def _generation_complete(self, result: str, output_path: Path):
        """Handle successful generation completion."""
        self.progress.stop()
        self.generate_button.config(state='normal')
        self.status_var.set("Configuration generated successfully!")
        
        if result:
            self.log_message("Configuration generation completed successfully!")
            self.log_message(f"Output saved to: {output_path}")
            self.log_message(f"Generated {len(result.splitlines())} lines")
            self.log_message("")
            self.log_message("Preview of generated changes.ini:")
            self.log_message("-" * 50)
            
            # Show preview of first 30 lines
            lines = result.splitlines()
            preview_lines = lines[:30]
            for line in preview_lines:
                self.log_message(line)
            
            if len(lines) > 30:
                self.log_message(f"... and {len(lines) - 30} more lines")
            
            messagebox.showinfo(
                "Success",
                f"Configuration file generated successfully!\n\n"
                f"File saved to: {output_path}\n"
                f"Lines generated: {len(lines)}"
            )
        else:
            self.log_message("No differences found between the paths.")
            self.log_message("The files/installations appear to be identical.")
            messagebox.showinfo(
                "No Changes",
                "No differences found between the selected paths.\n"
                "The files or installations appear to be identical."
            )
    
    def _generation_error(self, error_message: str):
        """Handle generation error."""
        self.progress.stop()
        self.generate_button.config(state='normal')
        self.status_var.set("Error occurred during generation")
        
        self.log_message(f"Error: {error_message}")
        messagebox.showerror("Generation Error", f"An error occurred:\n\n{error_message}")
    
    def log_message(self, message: str):
        """Add a message to the output text area."""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_output(self):
        """Clear the output text area."""
        self.output_text.delete(1.0, tk.END)
    
    def save_output(self):
        """Save the output text to a file."""
        content = self.output_text.get(1.0, tk.END)
        if not content.strip():
            messagebox.showwarning("No Content", "There is no output to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Output Log",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Output saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{e}")
    
    def show_about(self):
        """Show about dialog."""
        about_text = (
            "HoloGenerator v1.0.0\n\n"
            "KOTOR Configuration Generator for HoloPatcher\n\n"
            "Automatically generates changes.ini files by comparing\n"
            "KOTOR installations or individual files.\n\n"
            "Part of the PyKotor toolkit.\n"
            "© th3w1zard1"
        )
        messagebox.showinfo("About HoloGenerator", about_text)


def main():
    """Main function to run the GUI application."""
    if not TKINTER_AVAILABLE:
        print("Error: tkinter is not available. Please install tkinter to use the GUI.")
        sys.exit(1)
    
    try:
        root = tk.Tk()
        
        # Set up themed styles
        style = ttk.Style()
        try:
            style.theme_use('clam')  # Use a modern theme
        except tk.TclError:
            pass  # Use default theme if clam is not available
        
        # Configure styles
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        app = HoloGeneratorGUI(root)
        
        # Handle window close event
        def on_closing():
            if messagebox.askokcancel("Quit", "Do you want to quit?"):
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the GUI event loop
        root.mainloop()
        
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()