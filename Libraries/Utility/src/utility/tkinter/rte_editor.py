# Code taken from https://thepythoncode.com/code/create-rich-text-editor-with-tkinter-python
from __future__ import annotations

import ctypes
import json
import tkinter as tk

from functools import partial
from tkinter.filedialog import askopenfilename, asksaveasfilename
from typing import Any

from utility.system.path import Path

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
}


def main():
    # Handle File Events
    def handle_file_manager(event: tk.Tk | None = None, action=None):
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

    def resetTags():
        for tag in text_area.tag_names():
            text_area.tag_remove(tag, "1.0", "end")

        for tag_type in tag_types:
            text_area.tag_configure(tag_type.lower(), tag_types[tag_type])

    def keyDown(event: tk.Tk | None = None):
        root.title(f"{app_name} - *{file_path}")

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
    # Setup
    root = tk.Tk()
    root.geometry("600x600")

    # Used to make title of the application
    app_name = "Rich Text Editor"
    root.title(app_name)

    text_area = tk.Text(root, font=f"{font_name} 15", relief=tk.FLAT)
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
        format_menu.add_command(label=tag_type, command=partial(tagToggle, tag_name=tag_type.lower()))

    root.mainloop()

if __name__ == "__main__":
    main()
