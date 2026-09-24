"""
Lightweight hover tooltip component for CustomTkinter and Tkinter widgets.
Non-intrusive, theme-aware, with configurable display delay and automatic cleanup.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Optional


class CTkToolTip:
    """
    Attaches a tooltip to any widget that appears on hover after a short delay.
    """
    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        delay_ms: int = 400,
        wrap_length: int = 260,
    ):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.wrap_length = wrap_length
        self.tip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def set_text(self, text: str) -> None:
        self.text = text

    def _on_enter(self, event=None) -> None:
        self._schedule()

    def _on_leave(self, event=None) -> None:
        self._cancel()
        self._hide()

    def _schedule(self) -> None:
        self._cancel()
        if not self.text:
            return
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except Exception:
            pass

    def _cancel(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if not self.text or self.tip_window is not None:
            return

        try:
            # Position tooltip just below the widget
            x = self.widget.winfo_rootx() + 15
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

            mode = ctk.get_appearance_mode().lower()
            bg_color = "#1A202C" if mode == "dark" else "#FFFFFF"
            fg_color = "#EDF2F7" if mode == "dark" else "#1A202C"
            border_color = "#4A5568" if mode == "dark" else "#CBD5E0"

            self.tip_window = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            try:
                tw.attributes("-topmost", True)
            except Exception:
                pass

            frame = tk.Frame(
                tw,
                background=bg_color,
                highlightbackground=border_color,
                highlightthickness=1,
                padx=8,
                pady=5,
            )
            frame.pack()

            label = tk.Label(
                frame,
                text=self.text,
                justify="left",
                background=bg_color,
                foreground=fg_color,
                font=("Helvetica", 9),
                wraplength=self.wrap_length,
            )
            label.pack()
        except Exception:
            self._hide()

    def _hide(self) -> None:
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None


def create_tooltip(widget, text: str) -> Optional[CTkToolTip]:
    """Helper to attach a tooltip to a widget if text is non-empty."""
    if not text:
        return None
    return CTkToolTip(widget, text)
