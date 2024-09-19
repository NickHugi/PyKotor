from __future__ import annotations

import tkinter as tk

from typing import TYPE_CHECKING

from utility.common.misc_string.util import insert_newlines

if TYPE_CHECKING:
    from collections.abc import Callable
    from tkinter import ttk


class ToolTip:
    def __init__(
        self,
        widget: ttk.Widget,
        callable_returns_text: Callable[..., str],
        wordwrap_at_limit: int = 100,
    ):
        self.widget: ttk.Widget = widget
        self.get_tooltip_text: Callable[..., str] = callable_returns_text
        self.tip_window: tk.Toplevel | None = None
        self.wordwrap_at_limit: int = wordwrap_at_limit

        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event: tk.Event | None = None):
        """Display text in a tooltip window."""
        text = self.get_tooltip_text().strip()
        text = insert_newlines(text, self.wordwrap_at_limit)
        if not text:
            return
        bbox: tuple[int, int, int, int] | None = self.widget.bbox("insert")
        if bbox is None:
            return

        x, y, _, _ = bbox
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(boolean=True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tip_window, text=text, justify=tk.LEFT, background="#ffffff", relief=tk.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event: tk.Event | None = None):
        """Destroy the tooltip window."""
        tw: tk.Toplevel | None = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()
