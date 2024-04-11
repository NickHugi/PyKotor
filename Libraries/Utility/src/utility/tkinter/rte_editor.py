# Code taken from https://thepythoncode.com/code/create-rich-text-editor-with-tkinter-python
from __future__ import annotations

import ctypes
import json
import os
import re
import tkinter as tk

from contextlib import suppress
from functools import partial
from tkinter import colorchooser
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
# Common fonts
fonts = ["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana", "Georgia", "Palatino", "Garamond", "Bookman", "Comic Sans MS"]
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

tag_categories = {
    "Font Styles": {
        "Bold": {"font": f"{font_name} 15 bold"},
        "Italic": {"font": f"{font_name} 15 italic"},
        "Underline": {"underline": True},
        "Overstrike": {"overstrike": True}
    },
    "Font Sizes": {
        "Small": {"font": f"{font_name} 8"},
        "Medium": {"font": f"{font_name} 12"},
        "Large": {"font": f"{font_name} 18"},
        "Extra Large": {"font": f"{font_name} 24"}
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
        "Right": {"justify": "right"},
        "Justify": {"justify": "full"}
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

    def apply_font(font_name):
        current_tags = text_area.tag_names("sel.first")
        for tag in current_tags:
            if tag.startswith("font_"):
                text_area.tag_remove(tag, "sel.first", "sel.last")
        tag_name = f"font_{font_name.replace(' ', '_')}"
        text_area.tag_configure(tag_name, font=(font_name, 12))
        text_area.tag_add(tag_name, "sel.first", "sel.last")

    def apply_font_size(size):
        tag_name = f"size_{size}"
        text_area.tag_configure(tag_name, font=(None, size))
        text_area.tag_add(tag_name, "sel.first", "sel.last")

    def apply_color(color_type):
        color_code = colorchooser.askcolor(title=f"Choose {color_type} Color")[1]
        if color_code:
            tag_name = f"{color_type}_{color_code}"
            text_area.tag_configure(tag_name, **{color_type: color_code})
            text_area.tag_add(tag_name, "sel.first", "sel.last")

    def undo():
        with suppress(tk.TclError):
            text_area.edit_undo()

    def redo():
        with suppress(tk.TclError):
            text_area.edit_redo()

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
                elif list_type == "bullet":
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

    def apply_tag_from_category(category, option):
        if category in ["Text Colors", "Background Colors"] and option == "Custom Color...":
            apply_color(color_type=(category == "Text Colors"))
        elif category == "Lists":
            if option == "Bullet List":
                # Your implementation for applying bullet list
                pass
            elif option == "Numbered List":
                # Your implementation for applying numbered list
                pass
        else:
            # General case for applying tags
            properties = tag_categories[category][option]
            tag_name = f"{category}_{option}"
            text_area.tag_configure(tag_name, **properties)
            text_area.tag_add(tag_name, "sel.first", "sel.last")


    def toggle_format(tag, properties=None):
        """Toggle formatting for the selected text based on the tag.

        If properties are given, configure the tag with these properties.
        """
        if properties:
            text_area.tag_configure(tag, **properties)
        current_tags = text_area.tag_names("sel.first")
        if tag in current_tags:
            text_area.tag_remove(tag, "sel.first", "sel.last")
        else:
            text_area.tag_add(tag, "sel.first", "sel.last")

    def check_menu_item(menu, index, tag):
        """Check or uncheck the menu item based on whether the tag is applied to the current selection."""
        current_tags = text_area.tag_names("sel.first")
        if tag in current_tags:
            menu.entryconfig(index, onvalue=1)
        else:
            menu.entryconfig(index, onvalue=0)

    def build_format_menu(menu):
        """Dynamically build the format menu with checkable items based on tag_categories."""
        for category, options in tag_categories.items():
            submenu = tk.Menu(menu, tearoff=0)
            menu.add_cascade(label=category, menu=submenu)
            for option, properties in options.items():
                tag_name = f"{category}_{option}".replace(" ", "_")
                if isinstance(properties, dict):
                    submenu.add_checkbutton(label=option, command=partial(toggle_format, tag_name, properties))
                else:
                    submenu.add_command(label=option, command=lambda c=category, o=option: apply_tag_from_category(c, o))
                # Update check status when opening the menu
                menu.bind("<Enter>", lambda event, menu=submenu, tag=tag_name, index=submenu.index(option): check_menu_item(menu, index, tag), add="+")

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

    # Font Menu
    font_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Fonts", menu=font_menu)
    for f in fonts:
        font_menu.add_command(label=f, command=lambda f=f: apply_font(f))

    build_format_menu(menu)  # Reuse the build_format_menu function

    format_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="Format", menu=format_menu)

    color_menu = tk.Menu(format_menu, tearoff=0)
    format_menu.add_cascade(label="Color", menu=color_menu)
    color_menu.add_command(label="Text Color", command=lambda: apply_color("foreground"))
    color_menu.add_command(label="Background Color", command=lambda: apply_color("background"))

    size_menu = tk.Menu(format_menu, tearoff=0)
    format_menu.add_cascade(label="Size", menu=size_menu)
    for size in range(8, 25):  # Example sizes
        size_menu.add_command(label=str(size), command=lambda size=size: apply_font_size(size))

    for tag_type in tag_types:
        if tag_type.startswith("Align"):
            continue
        format_menu.add_command(label=tag_type, command=partial(tagToggle, tag_name=tag_type.lower()))
    format_menu.add_separator()
    format_menu.add_command(label="Bullet List", command=lambda: apply_list("bullet"))
    format_menu.add_command(label="Numbered List", command=lambda: apply_list("number"))
    format_menu.add_separator()
    format_menu.add_command(label="Align Left", command=lambda: align_text("align_left"))
    format_menu.add_command(label="Align Center", command=lambda: align_text("align_center"))
    format_menu.add_command(label="Align Right", command=lambda: align_text("align_right"))

    # Context (right-click) menu setup
    def show_context_menu(event):
        """Show the right-click context menu."""
        try:
            format_menu.tk_popup(event.x_root, event.y_root)
        finally:
            format_menu.grab_release()
    build_format_menu(format_menu)  # Reuse the build_format_menu function

    text_area.bind("<Button-3>", show_context_menu)

    # Bind the undo and redo functions to Ctrl+Z and Ctrl+Y
    root.bind_all("<Control-z>", lambda _event: undo())
    root.bind_all("<Control-y>", lambda _event: redo())
    root.bind_all("<Control-Shift-z>", lambda _event: redo())
    root.bind_all("<Control-Shift-Z>", lambda _event: redo())  # different keyboard layouts ig

    root.mainloop()


if __name__ == "__main__":
    main()
