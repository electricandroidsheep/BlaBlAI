"""
Main Application Window Controller.
Manages theme settings, locale initialization, window lifecycle, and transitions between
HubView (Google Docs-style dashboard) and EditorView (Document Workspace).
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Optional

from storage import StorageManager
from models import ProtocolDocument
from gui.hub_view import HubView
from gui.editor_view import EditorView
from gui.assets import ensure_icon_file
from i18n import (
    t,
    set_current_locale,
    get_current_locale,
)


class MainWindow(ctk.CTk):
    def __init__(self, storage: Optional[StorageManager] = None):
        super().__init__()
        self.storage = storage or StorageManager()

        # Initialize locale and appearance theme from persistent storage
        set_current_locale(self.storage.ui_locale)
        ctk.set_appearance_mode(self.storage.ui_theme)
        ctk.set_default_color_theme("blue")

        self.title(t("app_window_title"))
        self.geometry("1200x840")
        self.minsize(980, 680)

        # Set application vector icon
        try:
            icon_p = ensure_icon_file()
            if icon_p.exists():
                self._app_icon = tk.PhotoImage(file=str(icon_p))
                self.iconphoto(False, self._app_icon)
        except Exception:
            pass

        self._center_window()

        self.current_view: Optional[ctk.CTkFrame] = None
        self.active_doc: Optional[ProtocolDocument] = None

        self.show_hub()

    def _center_window(self):
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = 1200
            h = 840
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self.storage.ui_theme = new_theme.lower()

    def on_language_changed(self, new_locale: str):
        self.title(t("app_window_title"))

    def show_hub(self):
        """Switches to the Google Docs-style Hub start screen."""
        if self.current_view:
            self.current_view.destroy()

        self.active_doc = None
        self.current_view = HubView(
            self,
            storage=self.storage,
            on_open_document=self.open_document,
            on_toggle_theme=self.toggle_theme,
            on_language_changed=self.on_language_changed,
        )
        self.current_view.pack(fill="both", expand=True)

    def open_document(self, doc: ProtocolDocument):
        """Switches to the Editor Workspace for the specified document."""
        if self.current_view:
            self.current_view.destroy()

        self.active_doc = doc
        self.current_view = EditorView(
            self,
            doc=doc,
            storage=self.storage,
            on_back_to_hub=self.show_hub,
        )
        self.current_view.pack(fill="both", expand=True)
