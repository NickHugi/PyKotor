from __future__ import annotations

import ctypes
import logging
import os
import pathlib
import sys
import tkinter as tk

from contextlib import suppress
from pathlib import Path
from threading import Event, Thread
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import TYPE_CHECKING, cast

if not getattr(sys, "frozen", False):

    def update_sys_path(path):
        working_dir = str(path)
        if working_dir not in sys.path:
            sys.path.append(working_dir)

    with suppress(Exception):
        pykotor_path = pathlib.Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
    with suppress(Exception):
        utility_path = pathlib.Path(__file__).parents[4] / "Libraries" / "Utility" / "src" / "utility"
        if utility_path.exists():
            update_sys_path(utility_path.parent)
    with suppress(Exception):
        update_sys_path(pathlib.Path(__file__).parents[1])

from loggerplus import RobustLogger  # noqa: E402

from kitgenerator import __version__  # noqa: E402
from kitgenerator.extract import extract_kit  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.path import CaseAwarePath, find_kotor_paths_from_default  # noqa: E402
from pykotor.tslpatcher.logger import LogType, PatchLog, PatchLogger  # noqa: E402
from utility.error_handling import universal_simplify_exception  # noqa: E402

if TYPE_CHECKING:
    from argparse import Namespace

VERSION_LABEL = __version__


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"KitGenerator {VERSION_LABEL}")

        self.set_window(width=600, height=500)

        # Map the title bar's X button to our handle_exit_button function
        self.root.protocol("WM_DELETE_WINDOW", self.handle_exit_button)

        self.task_running: bool = False
        self.task_thread: Thread | None = None
        self.installation_path: str = ""
        self.module_name: str = ""
        self.output_path: str = ""
        self.kit_id: str = ""
        self.pykotor_logger = RobustLogger()
        self.one_shot: bool = False
        self.log_level = None  # Will be set if needed for filtering
        self.current_installation: Installation | None = None

        self.initialize_logger()
        self.initialize_ui_controls()
        self.show_onboarding_info()

        cmdline_args: Namespace | None = None
        try:
            from kitgenerator.cli import parse_args

            cmdline_args = parse_args()
            self.execute_commandline(cmdline_args)
        except Exception:  # noqa: BLE001
            pass  # No CLI args or parsing failed, continue with GUI

        self.pykotor_logger.debug("Init complete")

    def set_window(
        self,
        width: int,
        height: int,
    ):
        # Get screen dimensions
        screen_width: int = self.root.winfo_screenwidth()
        screen_height: int = self.root.winfo_screenheight()

        # Calculate position to center the window
        x_position = int((screen_width / 2) - (width / 2))
        y_position = int((screen_height / 2) - (height / 2))

        # Set the dimensions and position
        self.root.geometry(f"{width}x{height}+{x_position}+{y_position}")
        self.root.resizable(width=True, height=True)
        self.root.minsize(width=width, height=height)

    def initialize_logger(self):
        self.logger = PatchLogger()
        self.logger.verbose_observable.subscribe(self.write_log)
        self.logger.note_observable.subscribe(self.write_log)
        self.logger.warning_observable.subscribe(self.write_log)
        self.logger.error_observable.subscribe(self.write_log)

    def initialize_ui_controls(self):
        # Use grid layout for main window
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure style for Combobox
        ttk.Style(self.root).configure("TCombobox", font=("Helvetica", 10), padding=4)

        # Top area for input fields and buttons
        top_frame: tk.Frame = tk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_frame.grid_columnconfigure(0, weight=0, minsize=80)  # Labels fixed width with minimum
        top_frame.grid_columnconfigure(1, weight=1)  # Make input fields expand
        top_frame.grid_columnconfigure(2, weight=0)  # Keep buttons fixed size

        # Store all discovered KOTOR install paths
        tk.Label(top_frame, text="Installation:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.installation_paths = ttk.Combobox(top_frame, style="TCombobox")
        self.installation_paths.set("Select your KOTOR directory path")
        self.installation_paths.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.installation_paths["values"] = [str(path) for game in find_kotor_paths_from_default().values() for path in game]
        self.installation_paths.bind("<<ComboboxSelected>>", self.on_installation_paths_chosen)
        # Browse for a KOTOR path
        self.installation_browse_button = ttk.Button(top_frame, text="Browse", command=self.browse_installation)
        self.installation_browse_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        # Module name - changed to combobox
        tk.Label(top_frame, text="Module:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.module_combobox = ttk.Combobox(top_frame, style="TCombobox", state="readonly")
        self.module_combobox.set("Select a module (choose installation first)")
        self.module_combobox.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.module_combobox.bind("<<ComboboxSelected>>", self.on_module_selected)

        # Output path
        tk.Label(top_frame, text="Output:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.output_entry = tk.Entry(top_frame)
        self.output_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        tk.Button(top_frame, text="Browse", command=self.browse_output).grid(row=2, column=2, padx=5, pady=2)

        # Kit ID (optional)
        tk.Label(top_frame, text="Kit ID:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.kit_id_entry = tk.Entry(top_frame)
        self.kit_id_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        # Middle area for text and scrollbar
        text_frame = tk.Frame(self.root)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # Configure the text
        self.main_text = tk.Text(text_frame, wrap=tk.WORD)
        self.main_text.grid(row=0, column=0, sticky="nsew")
        self.set_text_font(self.main_text)

        # Create scrollbar for main frame
        scrollbar = tk.Scrollbar(text_frame, command=self.main_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_text.config(yscrollcommand=scrollbar.set)

        # Bottom area for buttons
        bottom_frame = tk.Frame(self.root)
        bottom_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.exit_button = ttk.Button(bottom_frame, text="Exit", command=self.handle_exit_button)
        self.exit_button.pack(side="left", padx=5, pady=5)
        self.extract_button = ttk.Button(bottom_frame, text="Extract", command=self.begin_extract)
        self.extract_button.pack(side="right", padx=5, pady=5)

        self.simple_thread_event: Event = Event()
        self.progress_value = tk.IntVar(value=0)

        # Progress bar
        self.progress_bar = ttk.Progressbar(bottom_frame, maximum=100, variable=self.progress_value)
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

    def set_text_font(
        self,
        text_frame: tk.Text,
    ):
        font_obj = tkfont.Font(font=text_frame.cget("font"))
        font_obj.configure(size=9)
        text_frame.configure(font=font_obj)

        # Define a bold and slightly larger font
        bold_font = tkfont.Font(font=text_frame.cget("font"))
        bold_font.configure(size=10, weight="bold")

        self.main_text.tag_configure("DEBUG", foreground="#6495ED")  # Cornflower Blue
        self.main_text.tag_configure("INFO", foreground="#000000")  # Black
        self.main_text.tag_configure("WARNING", foreground="#CC4E00", background="#FFF3E0", font=bold_font)  # Orange with bold font
        self.main_text.tag_configure("ERROR", foreground="#DC143C", font=bold_font)  # Firebrick with bold font
        self.main_text.tag_configure("CRITICAL", foreground="#FFFFFF", background="#8B0000", font=bold_font)  # White on Dark Red with bold font

    def on_installation_paths_chosen(
        self,
        event: tk.Event,
    ):
        """Adjust the combobox after a short delay and populate modules."""
        self.root.after(10, lambda: self.move_cursor_to_end(cast("ttk.Combobox", event.widget)))
        # Populate modules when installation is selected
        self.populate_modules()

    def move_cursor_to_end(
        self,
        combobox: ttk.Combobox,
    ):
        """Shows the rightmost portion of the specified combobox as that's the most relevant."""
        combobox.focus_set()
        position: int = len(combobox.get())
        combobox.icursor(position)
        combobox.xview(position)
        self.root.focus_set()

    def browse_installation(
        self,
        default_kotor_dir_str: os.PathLike | str | None = None,
    ):
        """Opens the KOTOR directory.

        Args:
        ----
            default_kotor_dir_str: The default KOTOR directory path as a string. This is only relevant when using the CLI.

        Processing Logic:
        ----------------
            - Try to get the directory path from the default or by opening a file dialog
            - Set the installation_paths config value and add path to list if not already present
            - Move cursor after a delay to end of dropdown
            - Populate modules for the selected installation
        """
        try:
            directory_path_str: os.PathLike | str = default_kotor_dir_str or filedialog.askdirectory(title="Select KOTOR Installation Directory")
            if not directory_path_str:
                return
            directory = CaseAwarePath(directory_path_str)
            directory_str = str(directory)
            self.installation_paths.set(str(directory))
            if directory_str not in self.installation_paths["values"]:
                self.installation_paths["values"] = (*self.installation_paths["values"], directory_str)
            self.root.after(10, self.move_cursor_to_end, self.installation_paths)
            # Populate modules when installation is selected
            self.populate_modules()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred while loading the game directory.")

    def populate_modules(self):
        """Populate the module combobox with modules from the selected installation."""
        installation_path: str = self.installation_paths.get().strip()
        if not installation_path or installation_path == "Select your KOTOR directory path":
            self.module_combobox["values"] = []
            self.module_combobox.set("Select a module (choose installation first)")
            self.module_combobox.config(state="readonly")
            # Clear kit ID when installation is cleared
            self.kit_id_entry.delete(0, tk.END)
            return

        try:
            # Create installation object
            self.current_installation = Installation(Path(installation_path))
            modules: list[str] = self.current_installation.modules_list()

            # Format modules similar to HolocronToolset: "Area Name [module_name.rim]"
            # For now, just show module names (we can enhance with area names later)
            module_values: list[str] = []
            seen_stems: set[str] = set()
            for module in sorted(modules):
                # Normalize module name for display
                module_stem = Path(module).stem.lower()
                # Skip _s.rim files (data files) - show main module only
                if module_stem.endswith("_s"):
                    continue
                # Avoid duplicates
                if module_stem in seen_stems:
                    continue
                seen_stems.add(module_stem)
                module_values.append(f"{module_stem} [{module}]")

            self.module_combobox["values"] = module_values
            if module_values:
                self.module_combobox.set("Select a module")
                self.module_combobox.config(state="readonly")
            else:
                self.module_combobox.set("No modules found")
                self.module_combobox.config(state="readonly")
            # Clear previous selections when installation changes
            self.kit_id_entry.delete(0, tk.END)
        except Exception as e:  # noqa: BLE001
            self.module_combobox["values"] = []
            self.module_combobox.set("Invalid installation")
            self.module_combobox.config(state="readonly")
            self._handle_general_exception(e, "Failed to load modules from installation", msgbox=False)

    def on_module_selected(self, event: tk.Event):
        """Handle module selection - auto-populate Kit ID."""
        selected_module: str = self.module_combobox.get().strip()
        if not selected_module or selected_module in ("Select a module", "Select a module (choose installation first)", "No modules found", "Invalid installation"):
            return

        # Extract module name from combobox display format
        if " [" in selected_module and "]" in selected_module:
            # Format: "module_name [module_name.rim]"
            module_name = selected_module.split(" [")[-1].rstrip("]")
        else:
            module_name = selected_module

        # Normalize module name (strip extension and path)
        module_path = Path(module_name)
        module_name_clean: str = module_path.stem.lower()

        # Auto-populate Kit ID if it's empty or still has the default
        current_kit_id: str = self.kit_id_entry.get().strip()
        if not current_kit_id:
            self.kit_id_entry.delete(0, tk.END)
            self.kit_id_entry.insert(0, module_name_clean)

    def browse_output(self):
        directory: str | None = filedialog.askdirectory(title="Select Output Directory")
        if directory and directory.strip():
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)

    def execute_commandline(
        self,
        cmdline_args: Namespace | None,
    ):
        """Handle command line arguments passed to the application."""
        if cmdline_args is None:
            return

        if cmdline_args.installation:
            self.browse_installation(cmdline_args.installation)
        if cmdline_args.module:
            # Try to set in combobox if it exists, otherwise set directly
            if hasattr(self, 'module_combobox'):
                # Find the module in the combobox values
                module_values: list[str] = self.module_combobox["values"]
                module_normalized: str = Path(cmdline_args.module).stem.lower()
                for value in module_values:
                    if module_normalized in value.lower():
                        self.module_combobox.set(value)
                        self.on_module_selected(tk.Event())
                        break
                else:
                    # Module not in list, set it directly (will be normalized)
                    self.module_combobox.set(str(cmdline_args.module))
                    self.on_module_selected(tk.Event())
        if cmdline_args.output:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, cmdline_args.output)
        if cmdline_args.kit_id:
            self.kit_id_entry.delete(0, tk.END)
            self.kit_id_entry.insert(0, cmdline_args.kit_id)

        # Check if we should run in CLI mode
        if cmdline_args.installation and cmdline_args.module and cmdline_args.output:
            # All required args provided, run in one-shot mode
            self.one_shot = bool(cmdline_args.console)
            if not cmdline_args.console:
                self.hide_console()
            self.begin_extract_thread(self.simple_thread_event)

    def hide_console(self):
        """Hide the console window in GUI mode."""
        # Windows
        if os.name == "nt":
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def handle_exit_button(self):
        """Handle exit button click during extraction."""
        if not self.task_running or not self.task_thread or not self.task_thread.is_alive():
            print("Goodbye!")
            sys.exit(0)
            return

        # Handle unsafe exit
        if self.task_running and not messagebox.askyesno(
            "Really cancel the current extraction?",
            "A task is currently running. Exiting now may not be safe. Really continue?",
        ):
            return
        self.simple_thread_event.set()
        import time

        time.sleep(1)
        print("Extraction thread is still alive, attempting force close...")
        i = 0
        while self.task_thread.is_alive():
            try:
                self.task_thread._stop()  # type: ignore[attr-defined]  # pylint: disable=protected-access  # noqa: SLF001
                print("force terminate of extraction thread succeeded")
            except BaseException as e:  # pylint: disable=W0718  # noqa: BLE001
                self._handle_general_exception(e, "Error using self.task_thread._stop()", msgbox=False)
            print(f"Extraction thread is still alive after {i} seconds, waiting...")
            time.sleep(1)
            i += 1
            if i == 2:
                break

        print("Destroying self")
        self.root.destroy()
        print("Goodbye!")
        sys.exit(0)

    def _handle_general_exception(
        self,
        exc: BaseException,
        custom_msg: str = "Unexpected error.",
        title: str = "",
        *,
        msgbox: bool = True,
    ):
        self.pykotor_logger.exception(custom_msg, exc_info=exc)
        error_name, msg = universal_simplify_exception(exc)
        if msgbox:
            messagebox.showerror(
                title or error_name,
                f"{(error_name + os.linesep * 2) if title else ''}{custom_msg}.{os.linesep * 2}{msg}",
            )

    def pre_extract_validate(self) -> bool:
        """Validates prerequisites for starting an extraction."""
        if self.task_running:
            messagebox.showinfo(
                "Task already running",
                "Wait for the previous task to finish.",
            )
            return False

        installation_path = self.installation_paths.get().strip()
        if not installation_path:
            messagebox.showinfo(
                "No installation path",
                "Select your KOTOR installation directory first.",
            )
            return False

        module_name = self.module_combobox.get().strip()
        if not module_name or module_name == "Select a module (choose installation first)":
            messagebox.showinfo(
                "No module selected",
                "Select a module first.",
            )
            return False
        # Extract module name from combobox display format if needed
        if " [" in module_name and "]" in module_name:
            # Format: "Area Name [module_name.rim]"
            module_name = module_name.split(" [")[-1].rstrip("]")

        output_path = self.output_entry.get().strip()
        if not output_path:
            messagebox.showinfo(
                "No output path",
                "Select an output directory first.",
            )
            return False

        # Validate installation path
        try:
            Installation(Path(installation_path))
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(
                "Invalid installation path",
                f"The installation path is invalid: {e}",
            )
            return False

        # Check access to output directory
        case_output_path = CaseAwarePath(output_path)
        if not case_output_path.exists():
            try:
                case_output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:  # noqa: BLE001
                messagebox.showerror(
                    "Cannot create output directory",
                    f"Cannot create output directory: {e}",
                )
                return False

        return True

    def begin_extract(self):
        """Starts the extraction process in a background thread."""
        self.pykotor_logger.debug("Call begin_extract")
        try:
            if not self.pre_extract_validate():
                return
            self.pykotor_logger.debug("Prevalidate finished, starting extract thread")
            self.task_thread = Thread(target=self.begin_extract_thread, args=(self.simple_thread_event,), name="KitGenerator_extract_thread")
            self.task_thread.start()
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_general_exception(e, "An unexpected error occurred during the extraction and the program was forced to exit")
            sys.exit(1)

    def begin_extract_thread(
        self,
        should_cancel_thread: Event,
    ):
        """Starts the kit extraction thread."""
        self.pykotor_logger.debug("begin_extract_thread reached")

        installation_path = Path(self.installation_paths.get().strip())
        module_name = self.module_combobox.get().strip()
        # Extract module name from combobox display format if needed
        if " [" in module_name and "]" in module_name:
            # Format: "Area Name [module_name.rim]"
            module_name = module_name.split(" [")[-1].rstrip("]")
        # Normalize module name (strip extension and path)
        module_path = Path(module_name)
        module_name = module_path.stem.lower()
        output_path = Path(self.output_entry.get().strip())
        kit_id = self.kit_id_entry.get().strip() or None

        # Store paths for log file
        self.installation_path = str(installation_path)
        self.module_name = module_name
        self.output_path = str(output_path)
        self.kit_id = kit_id or ""

        self.pykotor_logger.debug("set ui state")
        self.set_state(state=True)
        self.clear_main_text()
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, f"Starting kit extraction...{os.linesep}")
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)

        try:
            # Create installation object
            installation = Installation(installation_path)
            self.logger.add_note(f"Loaded installation from: {installation_path}")

            # Extract kit
            # Bridge RobustLogger to PatchLogger for UI display
            class LoggerBridge(logging.Handler):
                def __init__(self, patch_logger):
                    super().__init__()
                    self.patch_logger = patch_logger

                def emit(self, record):
                    msg = self.format(record)
                    if record.levelno >= logging.ERROR:
                        self.patch_logger.add_error(msg)
                    elif record.levelno >= logging.WARNING:
                        self.patch_logger.add_warning(msg)
                    elif record.levelno >= logging.INFO:
                        self.patch_logger.add_note(msg)
                    else:
                        self.patch_logger.add_verbose(msg)

            bridge = LoggerBridge(self.logger)
            bridge.setFormatter(logging.Formatter("%(message)s"))
            self.pykotor_logger.addHandler(bridge)

            try:
                extract_kit(
                    installation,
                    module_name,
                    output_path,
                    kit_id=kit_id,
                    logger=self.pykotor_logger,
                )
            finally:
                self.pykotor_logger.removeHandler(bridge)

            self.logger.add_note("Kit extraction completed successfully!")
            if not self.one_shot:
                messagebox.showinfo(
                    "Extraction complete!",
                    f"Kit generated successfully at: {output_path}",
                )
            else:
                sys.exit(0)
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            self._handle_exception_during_extract(e)
        finally:
            self.set_state(state=False)

    def set_state(
        self,
        *,
        state: bool,
    ):
        """Sets the active thread task state. Disables UI controls until this function is called again with state=False."""
        if state:
            self.progress_bar["value"] = 0
            self.progress_bar["maximum"] = 100
            self.progress_value.set(0)
            self.task_running = True
            self.extract_button.config(state=tk.DISABLED)
            self.installation_browse_button.config(state=tk.DISABLED)
            self.module_combobox.config(state=tk.DISABLED)
        else:
            self.task_running = False
            self.initialize_logger()  # reset the errors/warnings etc
            self.extract_button.config(state=tk.NORMAL)
            self.installation_browse_button.config(state=tk.NORMAL)
            self.module_combobox.config(state="readonly")

    def clear_main_text(self):
        self.main_text.config(state=tk.NORMAL)
        self.main_text.delete(1.0, tk.END)
        for tag in self.main_text.tag_names():
            if tag not in ["sel"]:
                self.main_text.tag_delete(tag)
        self.main_text.config(state=tk.DISABLED)

    def _handle_exception_during_extract(
        self,
        e: Exception,
    ):
        """Handles exceptions during extraction."""
        self.pykotor_logger.exception("Unhandled exception in KitGenerator", exc_info=e)
        error_name, msg = universal_simplify_exception(e)
        self.logger.add_error(f"{error_name}: {msg}{os.linesep}The extraction was aborted with errors")
        messagebox.showerror(
            error_name,
            f"An unexpected error occurred during the extraction and the extraction was forced to terminate.{os.linesep * 2}{msg}",
        )
        if self.one_shot:
            sys.exit(1)

    @property
    def log_file_path(self) -> Path:
        """Returns the path to the log file."""
        if self.output_path:
            return Path(self.output_path) / "kitgenerator_log.txt"
        return Path.cwd() / "kitgenerator_log.txt"

    def show_onboarding_info(self):
        """Display onboarding information in the log area on startup."""
        onboarding_text = f"""KitGenerator v{VERSION_LABEL}
{'=' * 80}
Extract kit resources from KOTOR module files (RIM/ERF)

Configuration:
{'=' * 80}

1. Installation:
   Select your KOTOR installation directory.
   Example: C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor
   Or: /home/user/.steam/steamapps/common/swkotor

2. Module:
   Select a module from the dropdown (populated after selecting installation).
   Examples:
     - danm13 (for danm13.rim / danm13_s.rim)
     - m15aa (for m15aa.rim / m15aa_s.rim)
   
   Supported formats:
     - RIM files: .rim (searches for module_name.rim and module_name_s.rim)
     - ERF files: .erf, .mod, .hak, .sav

3. Output:
   Enter the directory where the kit should be generated.
   Example: C:\\Users\\You\\Desktop\\kits
   Or: ./output

4. Kit ID (Optional):
   Enter a kit ID for the generated kit (defaults to module name).
   This will be used as the folder name and in the JSON file.
   Press Enter to use the default.

{'=' * 80}
Ready to extract kit resources!
"""
        self.main_text.config(state=tk.NORMAL)
        self.main_text.insert(tk.END, onboarding_text, "INFO")
        self.main_text.see(tk.END)
        self.main_text.config(state=tk.DISABLED)

    def write_log(
        self,
        log: PatchLog,
    ):
        """Writes a message to the log."""

        def log_type_to_level() -> LogType:
            # Default to showing all logs if log_level not set
            if self.log_level is None:
                return LogType.VERBOSE
            # Map log levels (simplified - always show all for now)
            return LogType.VERBOSE

        def log_to_tag(this_log: PatchLog) -> str:
            if this_log.log_type == LogType.NOTE:
                return "INFO"
            if this_log.log_type == LogType.VERBOSE:
                return "DEBUG"
            return this_log.log_type.name

        try:
            # Write to log file
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file_path.open("a", encoding="utf-8") as log_file:
                log_file.write(f"{log.formatted_message}\n")
            if log.log_type.value < log_type_to_level().value:
                return
        except OSError as e:
            RobustLogger().error(f"Failed to write the log file at '{self.log_file_path}': {e.__class__.__name__}: {e}")

        try:
            self.main_text.config(state=tk.NORMAL)
            self.main_text.insert(tk.END, log.formatted_message + os.linesep, log_to_tag(log))
            self.main_text.see(tk.END)
            self.main_text.config(state=tk.DISABLED)
        except Exception as e:  # noqa: BLE001
            self.pykotor_logger.error(f"Failed to write log to UI: {e}")
