# Code taken from https://thepythoncode.com/code/create-rich-text-editor-with-tkinter-python
from __future__ import annotations

import ctypes
import json
import os
import re
import tkinter as tk

from contextlib import suppress
from functools import partial
from pathlib import Path
from tkinter import colorchooser, filedialog, font
from typing import Any

if os.name == "nt":
    ctypes.windll.shcore.SetProcessDpiAwareness(True)  # noqa: FBT003

class RichTextEditor:
    def __init__(self, master: tk.Tk, initialdir: Path | None = None):
        self.root: tk.Tk = master
        self.root.title("Rich Text Editor")
        self.initialdir = Path.cwd() if initialdir is None else initialdir
        self.root.geometry("800x600")
        self.default_content: dict[str, Any] = {"content": "", "tags": {}}
        self.valid_file_types: tuple[tuple[str, str], ...] = (
            ("Rich Text (JSON)", "*.rte"),
            ("All Files", "*.*"),
        )
        self.current_font = "Arial"
        self.tag_categories = {
            "Font Styles": {
                "Bold": {"font": f"{self.current_font} 15 bold"},
                "Italic": {"font": f"{self.current_font} 15 italic"},
                "Underline": {"underline": True},
                "Overstrike": {"overstrike": True}
            },
            "Font Sizes": {
                "Small": {"font": f"{self.current_font} 8"},
                "Medium": {"font": f"{self.current_font} 12"},
                "Large": {"font": f"{self.current_font} 18"},
                "Extra Large": {"font": f"{self.current_font} 24"}
            },
            "Text Colors": {
                "Black": {"foreground": "#000000"},
                "Red": {"foreground": "#FF0000"},
                "Green": {"foreground": "#00FF00"},
                "Blue": {"foreground": "#0000FF"},
                "Custom Color...": "custom_color"
            },
            "Background Colors": {
                "Yellow": {"background": "#FFFF00"},
                "Light Blue": {"background": "#ADD8E6"},
                "Light Green": {"background": "#90EE90"},
                "Custom Color...": "custom_background_color"
            },
            "Paragraph Alignment": {
                "Left": {"justify": "left"},
                "Center": {"justify": "center"},
                "Right": {"justify": "right"}
            },
            "Spacing": {
                "Single": {"spacing1": "0", "spacing3": "0"},
                "1.5": {"spacing1": "3", "spacing3": "3"},
                "Double": {"spacing1": "6", "spacing3": "6"}
            },
            "Indentation": {
                "No Indent": {"lmargin1": "0", "lmargin2": "0"},
                "First Line": {"lmargin1": "20", "lmargin2": "0"},
                "Hanging": {"lmargin1": "0", "lmargin2": "20"},
                "Both": {"lmargin1": "20", "lmargin2": "20"}
            },
            "Lists": {
                "Bullet List": "bullet_list",
                "Numbered List": "numbered_list"
            }
        }

        self.text_area = tk.Text(self.root, undo=True, wrap="word")
        self.text_area.pack(expand=True, fill=tk.BOTH)

        self.init_fonts()
        self.init_ui()
        self.file_path = None

    def init_fonts(self):
        self.font_families = font.families()
        self.default_font = font.Font(family="Arial", size=12)
        self.text_area.configure(font=self.default_font)

    def init_ui(self):
        self.menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())

        for category, options in self.tag_categories.items():
            submenu = tk.Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label=category, menu=submenu)
            for option, properties in options.items():
                tag_name = f"{category}_{option}".replace(" ", "_")
                if isinstance(properties, dict):
                    submenu.add_checkbutton(label=option, command=partial(self.toggle_format, tag_name, properties))
                else:
                    submenu.add_command(label=option, command=lambda c=category, o=option: self.apply_tag_from_category(c, o))
                # Update check status when opening the menu
                self.menu_bar.bind("<Enter>", lambda event, menu=submenu, tag=tag_name, index=submenu.index(option): self.check_menu_item(menu, index, tag), add="+")

        edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.text_area.edit_undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.text_area.edit_redo, accelerator="Ctrl+Y")
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        self.root.bind_all("<Control-z>", lambda _e: self.text_area.edit_undo())
        self.root.bind_all("<Control-y>", lambda _e: self.text_area.edit_redo())
        self.root.bind_all("<Control-Shift-z>", lambda _event: self.text_area.edit_redo())
        self.root.bind_all("<Control-Shift-Z>", lambda _event: self.text_area.edit_redo())  # different keyboard layouts ig

        font_menu = tk.Menu(self.menu_bar, tearoff=0)
        for family in self.font_families:
            font_menu.add_command(label=family, command=lambda f=family: self.apply_font(family))
        self.menu_bar.add_cascade(label="Font", menu=font_menu)
        # Context (right-click) menu setup
        def show_context_menu(event):
            """Show the right-click context menu."""
            try:
                self.menu_bar.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu_bar.grab_release()
        self.text_area.bind("<Button-3>", show_context_menu)
        self.root.config(menu=self.menu_bar)

    def tagToggle(self, tag_name: str):
        # Check if there is a selection
        with suppress(tk.TclError):
            start, end = self.text_area.tag_ranges("sel")
            if start == end:  # No text is selected
                return

            if tag_name in self.text_area.tag_names("sel.first"):
                self.text_area.tag_remove(tag_name, start, end)
            else:
                self.text_area.tag_add(tag_name, start, end)

    def apply_font(self, family):
        current_font = font.Font(font=self.text_area["font"])
        new_font = font.Font(family=family, size=current_font["size"])
        self.text_area.configure(font=new_font)

    def apply_font_size(self, size: int):
        tag_name = f"size_{size}"
        self.text_area.tag_configure(tag_name, font=(None, size))
        self.text_area.tag_add(tag_name, "sel.first", "sel.last")

    def apply_color(self, color_type):
        color_code = colorchooser.askcolor(title=f"Choose {color_type} Color")[1]
        if color_code:
            tag_name = f"{color_type}_{color_code}"
            # Ensure color_type is correctly passed as a keyword argument
            config_kwargs = {"foreground": color_code} if color_type else {"background": color_code}
            self.text_area.tag_configure(tag_name, **config_kwargs)
            self.text_area.tag_add(tag_name, "sel.first", "sel.last")

    def undo(self):
        with suppress(tk.TclError):
            self.text_area.edit_undo()

    def redo(self):
        with suppress(tk.TclError):
            self.text_area.edit_redo()

    def resetTags(self):
        for tag in self.text_area.tag_names():
            if tag not in ["sel"]:
                self.text_area.tag_delete(tag)

    def apply_list(self, list_type="bullet"):
        with suppress(tk.TclError):
            selection_start = self.text_area.index("sel.first")
            selection_end = self.text_area.index("sel.last")
            selected_text = self.text_area.get(selection_start, selection_end)

            # Determine if we're adding or removing list formatting
            if any(line.startswith("• ") for line in selected_text.splitlines()) and list_type == "bullet":
                process = "remove"
            elif any(re.match(r"^\d+\.\s", line) for line in selected_text.splitlines()) and list_type == "number":
                process = "remove"
            else:
                process = "add"

            # Process each line of the selected text
            new_text_lines = []
            for line in selected_text.splitlines():
                if process == "remove":
                    if list_type == "bullet" and line.startswith("• "):
                        # Remove bullet
                        new_text_lines.append(line[2:])
                    elif list_type == "number" and re.match(r"^\d+\.\s", line):
                        # Remove numbering
                        new_text_lines.append(re.sub(r"^\d+\.\s", "", line))
                    else:
                        # Line is not formatted, keep it as is
                        new_text_lines.append(line)
                elif list_type == "bullet":
                    new_text_lines.append(f"• {line}")
                elif list_type == "number":
                    # Add a placeholder for numbers; actual numbers will be added later
                    new_text_lines.append(f"{line}")

            # Replace the selected text with the new text
            self.text_area.delete(selection_start, selection_end)
            # If numbering and we're adding numbers, add them here
            if list_type == "number" and process == "add":
                new_text_lines = [f"{i+1}. {line}" for i, line in enumerate(new_text_lines)]
            self.text_area.insert(selection_start, "\n".join(new_text_lines))

    def align_text(self, alignment):
        # Get current selection or the current line if nothing is selected
        try:
            start_index = self.text_area.index("sel.first")
            end_index = self.text_area.index("sel.last")
        except tk.TclError:
            # If nothing is selected, get the current line
            start_index = self.text_area.index("insert linestart")
            end_index = self.text_area.index("insert lineend")

        # Remove any previous alignment tags from the selected range
        for align_tag in ("align_left", "align_center", "align_right"):
            self.text_area.tag_remove(align_tag, start_index, end_index)

        # Add the new alignment tag to the selected range
        self.text_area.tag_add(alignment, start_index, end_index)

    def apply_tag_from_category(self, category, option):
        if category in ["Text Colors", "Background Colors"] and option == "Custom Color...":
            self.apply_color(color_type=(category == "Text Colors"))
        elif category == "Lists":
            raise
        else:
            # General case for applying tags
            properties = self.tag_categories[category][option]
            tag_name = f"{category}_{option}"
            self.text_area.tag_configure(tag_name, **properties)
            self.text_area.tag_add(tag_name, "sel.first", "sel.last")


    def toggle_format(self, tag, properties=None):
        """Toggle formatting for the selected text based on the tag.

        If properties are given, configure the tag with these properties.
        """
        if properties:
            self.text_area.tag_configure(tag, **properties)
        current_tags = self.text_area.tag_names("sel.first")
        if tag in current_tags:
            self.text_area.tag_remove(tag, "sel.first", "sel.last")
        else:
            self.text_area.tag_add(tag, "sel.first", "sel.last")

    def rgbToHex(self, *args) -> str:
        rgb = args
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def check_menu_item(self, menu, index, tag):
        """Check or uncheck the menu item based on whether the tag is applied to the current selection."""
        current_tags = self.text_area.tag_names("sel.first")
        if tag in current_tags:
            menu.entryconfig(index, onvalue=1)
        else:
            menu.entryconfig(index, onvalue=0)

    def open_file(self):
        filePath: str = filedialog.askopenfilename(filetypes=self.valid_file_types, initialdir=self.initialdir)
        if not filePath:
            return

        self.file_path = Path(filePath)
        with self.file_path.open() as f:
            document: dict[str, Any] = json.loads(f.read())

        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", document["content"])
        self.resetTags()

        if "tag_configs" in document:
            for tag, config in document["tag_configs"].items():
                self.text_area.tag_configure(tag, **config)

        # Add To the Document
        for tag_name in document["tags"]:
            for tag_range in document["tags"][tag_name]:
                self.text_area.tag_add(tag_name, *tag_range)

        self.root.title(f"Rich Text Editor - {filePath}")

    def keyDown(self, event: tk.Tk | None = None):
        self.root.title(f"Rich Text Editor - *{self.file_path}")

    def save_file_content(self):
        if not self.file_path:
            self.save_as_file()
            return

        document = {"content": self.text_area.get("1.0", tk.END), "tags": {}, "tag_configs": {}}

        for tag_name in self.text_area.tag_names():
            if tag_name == "sel":
                continue

            ranges = self.text_area.tag_ranges(tag_name)
            document["tags"][tag_name] = [[str(ranges[i]), str(ranges[i + 1])] for i in range(0, len(ranges), 2)]

            config = {
                option: self.text_area.tag_cget(tag_name, option)
                for option in ["font", "foreground", "background", "underline", "overstrike", "justify", "lmargin1", "lmargin2", "spacing1", "spacing3"]
                if self.text_area.tag_cget(tag_name, option)
            }
            if config:
                document["tag_configs"][tag_name] = config

        if self.file_path.suffix.lower() != ".rte":
            self.file_path = self.file_path.with_suffix(".rte")

        with self.file_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(document))

        self.root.title(f"Rich Text Editor - {self.file_path.name}")

    def save_file(self):
        self.save_file_content()

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("All Files", "*.*"), ("Rich Text (JSON)", "*.rte")])
        if file_path:
            self.file_path = Path(file_path)
            self.save_file_content()

def main():
    root = tk.Tk()
    app = RichTextEditor(root)
    root.mainloop()
