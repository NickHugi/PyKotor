# Code taken from https://thepythoncode.com/code/create-rich-text-editor-with-tkinter-python
from __future__ import annotations

import ctypes
import json
import os
import re
import tkinter as tk

from contextlib import suppress
from functools import partial
from tkinter.filedialog import askopenfilename, asksaveasfilename
from typing import Any

from utility.system.path import Path

if os.name == "nt":
    ctypes.windll.shcore.SetProcessDpiAwareness(True)  # noqa: FBT003

# Current File Path
file_path = None

# initial directory to be the current directory
initialdir = "."

# Define File Types that can be choosen
valid_file_types: tuple[tuple[str, str], ...] = (
    ("Rich Text (JSON)", "*.rte"),
    ("All Files", "*.*"),
)

# Setting the font and Padding for the Text Area
font_name: str = "Bahnschrift"
padding: int = 60

# Infos about the Document are stored here
document = {}

# Default content of the File
default_content: dict[str, Any] = {
    "content": "",
    "tags": {
        "bold": [(), ()],
    },
}


# Transform rgb to hex
def rgbToHex(rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)

# Add Different Types of Tags that can be added to the document.
tag_types: dict[str, dict[str, str]] = {
    # Font Settings
    "Bold": {"font": f"{font_name} 15 bold"},
    "Italic": {"font": f"{font_name} 15 italic"},
    "Code": {"font": "Consolas 15", "background": rgbToHex((200, 200, 200))},
    # Sizes
    "Normal Size": {"font": f"{font_name} 15"},
    "Larger Size": {"font": f"{font_name} 25"},
    "Largest Size": {"font": f"{font_name} 35"},
    # Background Colors
    "Highlight": {"background": rgbToHex((255, 255, 0))},
    "Highlight Red": {"background": rgbToHex((255, 0, 0))},
    "Highlight Green": {"background": rgbToHex((0, 255, 0))},
    "Highlight Black": {"background": rgbToHex((0, 0, 0))},
    # Foreground /  Text Colors
    "Text White": {"foreground": rgbToHex((255, 255, 255))},
    "Text Grey": {"foreground": rgbToHex((200, 200, 200))},
    "Text Blue": {"foreground": rgbToHex((0, 0, 255))},
    "Text green": {"foreground": rgbToHex((0, 255, 0))},
    "Text Red": {"foreground": rgbToHex((255, 0, 0))},
    # Alignment options
    "Align Left": {"justify": "left"},
    "Align Center": {"justify": "center"},
    "Align Right": {"justify": "right"},
}


def main():  # sourcery skip: use-contextlib-suppress
    # Handle File Events
    def handle_file_manager(
        event: tk.Tk | None = None,
        action: str | None = None,
    ):
        global document
        global file_path

        # Open
        if action == "open":
            _prompt_user_file()
        elif action == "save":
            document = default_content
            document["content"] = text_area.get("1.0", tk.END)

            for tag_name in text_area.tag_names():
                if tag_name == "sel":
                    continue

                document["tags"][tag_name] = []

                ranges = text_area.tag_ranges(tag_name)

                for i, tagRange in enumerate(ranges[::2]):
                    some_list: list[list[str]] = document["tags"][tag_name]
                    some_list.append([str(tagRange), str(ranges[i + 1])])

            if not file_path:
                # ask the user for a filename with the native file explorer.
                newfilePath: str = asksaveasfilename(filetypes=valid_file_types, initialdir=initialdir)

                # Return in case the User Leaves the Window without
                # choosing a file to save
                if newfilePath is None:
                    return

                file_path = newfilePath

            if not file_path.endswith(".rte"):
                file_path += ".rte"

            with Path(file_path).open("w") as f:
                print("Saving at: ", file_path)
                f.write(json.dumps(document))

            root.title(f"{app_name} - {file_path}")

    def _prompt_user_file():
        # ask the user for a filename with the native file explorer.
        filePath: str = askopenfilename(filetypes=valid_file_types, initialdir=initialdir)
        if not filePath:
            return

        with Path(filePath).open() as f:
            document: dict[str, Any] = json.loads(f.read())

        # Delete Content
        text_area.delete("1.0", tk.END)

        # Set Content
        text_area.insert("1.0", document["content"])

        # Set Title
        root.title(f"{app_name} - {filePath}")

        # Reset all tags
        resetTags()

        # Add To the Document
        for tag_name in document["tags"]:
            for tagStart, tagEnd in document["tags"][tag_name]:
                text_area.tag_add(tag_name, tagStart, tagEnd)
                print(tag_name, tagStart, tagEnd)

    def undo():
        with suppress(tk.TclError):
            text_area.edit_undo()

    def redo():
        with suppress(tk.TclError):
            text_area.edit_redo()

    def apply_list(list_type="bullet"):
        # Check if there's a selection
        try:
            selection_start = text_area.index("sel.first")
            selection_end = text_area.index("sel.last")
            # Get the selected text
            selected_text = text_area.get(selection_start, selection_end)
            # Process each line of the selected text
            listified_text = ""
            if list_type == "bullet":
                bullet_char = "•"
                for line in selected_text.splitlines():
                    listified_text += f"{bullet_char} {line}\n"
            elif list_type == "number":
                for i, line in enumerate(selected_text.splitlines(), start=1):
                    listified_text += f"{i}. {line}\n"
            # Replace the selected text with the listified text
            text_area.delete(selection_start, selection_end)
            text_area.insert(selection_start, listified_text.rstrip())
        except tk.TclError:
            # If nothing is selected, do nothing
            pass

    def tagToggle(tag_name: str):
        # Check if there is a selection
        try:
            start, end = text_area.tag_ranges("sel")
            if start == end:  # No text is selected
                return

            if tag_name in text_area.tag_names("sel.first"):
                text_area.tag_remove(tag_name, start, end)
            else:
                text_area.tag_add(tag_name, start, end)

        except (ValueError, tk.TclError):
            # This block will execute if there is no selection, i.e., 'sel' tag doesn't exist
            ...

    def resetTags():
        for tag in text_area.tag_names():
            text_area.tag_remove(tag, "1.0", "end")

        for tag_type in tag_types:
            text_area.tag_configure(tag_type.lower(), tag_types[tag_type])
        text_area.tag_configure("align_left", justify="left")
        text_area.tag_configure("align_center", justify="center")
        text_area.tag_configure("align_right", justify="right")

    def keyDown(event: tk.Tk | None = None):
        root.title(f"{app_name} - *{file_path}")

    def apply_list(list_type="bullet"):
        try:
            selection_start = text_area.index("sel.first")
            selection_end = text_area.index("sel.last")
            selected_text = text_area.get(selection_start, selection_end)
            
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
                else:
                    if list_type == "bullet":
                        new_text_lines.append(f"• {line}")
                    elif list_type == "number":
                        # Add a placeholder for numbers; actual numbers will be added later
                        new_text_lines.append(f"{line}")

            # Replace the selected text with the new text
            text_area.delete(selection_start, selection_end)
            # If numbering and we're adding numbers, add them here
            if list_type == "number" and process == "add":
                new_text_lines = [f"{i+1}. {line}" for i, line in enumerate(new_text_lines)]
            text_area.insert(selection_start, "\n".join(new_text_lines))

        except tk.TclError:
            # If nothing is selected, do nothing
            pass

    def align_text(alignment):
        # Get current selection or the current line if nothing is selected
        try:
            start_index = text_area.index("sel.first")
            end_index = text_area.index("sel.last")
        except tk.TclError:
            # If nothing is selected, get the current line
            start_index = text_area.index("insert linestart")
            end_index = text_area.index("insert lineend")

        # Remove any previous alignment tags from the selected range
        for align_tag in ("align_left", "align_center", "align_right"):
            text_area.tag_remove(align_tag, start_index, end_index)

        # Add the new alignment tag to the selected range
        text_area.tag_add(alignment, start_index, end_index)

    # Setup
    root = tk.Tk()
    root.geometry("600x600")

    # Used to make title of the application
    app_name = "Rich Text Editor"
    root.title(app_name)

    text_area = tk.Text(root, font=f"{font_name} 15", relief=tk.FLAT, undo=True, autoseparators=True, maxundo=-1)
    text_area.pack(fill=tk.BOTH, expand=tk.TRUE, padx=padding, pady=padding)
    text_area.bind("<Key>", keyDown)

    resetTags()

    menu = tk.Menu(root)
    root.config(menu=menu)

    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="File", menu=file_menu)

    file_menu.add_command(label="Open", command=partial(handle_file_manager, action="open"), accelerator="Ctrl+O")
    root.bind_all("<Control-o>", partial(handle_file_manager, action="open"))

    file_menu.add_command(label="Save", command=partial(handle_file_manager, action="save"), accelerator="Ctrl+S")
    root.bind_all("<Control-s>", partial(handle_file_manager, action="save"))

    file_menu.add_command(label="Exit", command=root.destroy)

    format_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Format", menu=format_menu)

    for tag_type in tag_types:
        if tag_type.startswith("Align"):
            continue
        format_menu.add_command(label=tag_type, command=partial(tagToggle, tag_name=tag_type.lower()))
    format_menu.add_separator()
    format_menu.add_command(label="Bullet List", command=lambda: apply_list("bullet"))
    format_menu.add_command(label="Numbered List", command=lambda: apply_list("number"))
    format_menu.add_separator()
    format_menu.add_command(label="Align Left", command=lambda: align_text('align_left'))
    format_menu.add_command(label="Align Center", command=lambda: align_text('align_center'))
    format_menu.add_command(label="Align Right", command=lambda: align_text('align_right'))

    # Bind the undo and redo functions to Ctrl+Z and Ctrl+Y
    root.bind_all("<Control-z>", lambda _event: undo())
    root.bind_all("<Control-y>", lambda _event: redo())
    root.bind_all("<Control-Shift-z>", lambda _event: text_area.edit_redo())
    root.bind_all("<Control-Shift-Z>", lambda _event: text_area.edit_redo())  # different keyboard layouts ig

    root.mainloop()


if __name__ == "__main__":
    main()
