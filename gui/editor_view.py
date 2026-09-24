"""
Main Document Editor Workspace Container.
Coordinates navigation between Drop Logger, Fact-Check Matrix, and Preview/Export tabs.
Supports real-time language toggling (EN/DE) directly from the editor header.
"""

from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional

from models import ProtocolDocument, get_current_cest_time
from storage import StorageManager
from gui.metadata_dialog import MetadataDialog
from gui.logger_view import LoggerView
from gui.factcheck_view import FactCheckView
from gui.preview_view import PreviewView
from gui.assets import get_blablai_ctk_image
from gui.tooltip import create_tooltip
from i18n import (
    t,
    get_current_locale,
    set_current_locale,
    localize_scope,
)


class EditorView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        doc: ProtocolDocument,
        storage: StorageManager,
        on_back_to_hub: Callable[[], None],
    ):
        super().__init__(parent, fg_color="transparent")
        self.doc = doc
        self.storage = storage
        self.on_back_to_hub = on_back_to_hub

        self._build_ui()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # 1. Top Document Header Bar
        header = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        header.pack(fill="x", padx=16, pady=(12, 6))

        # Left: Back button & BlaBlAI Icon
        left_header = ctk.CTkFrame(header, fg_color="transparent")
        left_header.pack(side="left", padx=(12, 10), pady=10)

        btn_back = ctk.CTkButton(
            left_header,
            text=t("btn_back_to_hub"),
            width=135,
            height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray95"),
            hover_color=("gray70", "gray35"),
            command=self._handle_back,
        )
        btn_back.pack(side="left", padx=(0, 10))
        create_tooltip(btn_back, "Return to document hub. All changes are saved automatically.")

        self.editor_icon = get_blablai_ctk_image((28, 28))
        lbl_editor_icon = ctk.CTkLabel(left_header, image=self.editor_icon, text="")
        lbl_editor_icon.pack(side="left", padx=(0, 4))

        # Center: Document Info
        info_box = ctk.CTkFrame(header, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True, pady=6)

        self.lbl_doc_title = ctk.CTkLabel(
            info_box,
            text=self.doc.title,
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
            anchor="w",
        )
        self.lbl_doc_title.pack(anchor="w")

        self.lbl_doc_sub = ctk.CTkLabel(
            info_box,
            text=self._format_subtitle(),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            anchor="w",
        )
        self.lbl_doc_sub.pack(anchor="w")

        # Right: Edit Metadata, Language Toggle, & Auto-save Status
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right", padx=12, pady=10)

        self.lbl_save_status = ctk.CTkLabel(
            right_box,
            text=t("status_saved"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38a169",
        )
        self.lbl_save_status.pack(side="left", padx=(0, 10))

        # In-Editor Language Toggle Button (EN / DE)
        curr_loc = get_current_locale().upper()
        self.btn_lang = ctk.CTkButton(
            right_box,
            text=f"🌐 {curr_loc}",
            width=65,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray26"),
            text_color=("gray10", "gray90"),
            border_width=1,
            command=self._toggle_language,
        )
        self.btn_lang.pack(side="left", padx=(0, 8))
        create_tooltip(self.btn_lang, t("tooltip_lang"))

        btn_edit_meta = ctk.CTkButton(
            right_box,
            text=t("btn_edit_info"),
            width=100,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            command=self._handle_edit_metadata,
        )
        btn_edit_meta.pack(side="left")
        create_tooltip(btn_edit_meta, "Edit course, title, assignment scope, and author metadata.")

        # 2. Main Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color=("gray95", "gray14"))
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        self.tab_name_drops = t("tab_drops")
        self.tab_name_matrix = t("tab_matrix")
        self.tab_name_preview = t("tab_preview")

        tab_logger = self.tabview.add(self.tab_name_drops)
        tab_matrix = self.tabview.add(self.tab_name_matrix)
        tab_preview = self.tabview.add(self.tab_name_preview)

        # Instantiate subviews inside tabs
        self.logger_view = LoggerView(
            tab_logger,
            doc=self.doc,
            storage=self.storage,
            on_document_changed=self._on_document_changed,
        )
        self.logger_view.pack(fill="both", expand=True)

        self.matrix_view = FactCheckView(
            tab_matrix,
            doc=self.doc,
            on_document_changed=self._on_document_changed,
        )
        self.matrix_view.pack(fill="both", expand=True)

        self.preview_view = PreviewView(
            tab_preview,
            doc=self.doc,
            on_status_msg=self._set_status_message,
        )
        self.preview_view.pack(fill="both", expand=True)

        self.tabview.configure(command=self._on_tab_changed)

    def _format_subtitle(self) -> str:
        m = self.doc.metadata
        course = m.course_code_title or "General Course"
        scope = localize_scope(m.assignment_scope) if m.assignment_scope else "Assignment"
        examiner = f"  |  Examiner: {m.examiner}" if m.examiner else ""
        author = m.student_name or self.storage.student_name
        is_external = bool(m.student_name and m.student_name.strip() != self.storage.student_name.strip())
        ext_tag = f"  |  {t('lbl_external_author')}" if is_external else ""
        matrikel = f" [{m.matriculation_number}]" if m.matriculation_number else ""
        return f"{course} ({scope}){examiner}  |  👤 {author}{matrikel}{ext_tag}"

    def _toggle_language(self):
        new_loc = "de" if get_current_locale() == "en" else "en"
        set_current_locale(new_loc)
        self.storage.ui_locale = new_loc

        # Rebuild editor UI in place
        active_tab_index = 0
        try:
            curr = self.tabview.get()
            if curr == self.tab_name_matrix:
                active_tab_index = 1
            elif curr == self.tab_name_preview:
                active_tab_index = 2
        except Exception:
            pass

        self._build_ui()

        # Restore tab selection
        tabs = [self.tab_name_drops, self.tab_name_matrix, self.tab_name_preview]
        if active_tab_index < len(tabs):
            self.tabview.set(tabs[active_tab_index])

    def _on_document_changed(self):
        try:
            self.storage.save_document(self.doc)
            curr_time = get_current_cest_time().split(" ")[1]
            self.lbl_save_status.configure(text=t("status_saved_time", time=curr_time), text_color="#38a169")
        except Exception as e:
            self.lbl_save_status.configure(text=t("status_save_error"), text_color="#e53e3e")
            print(f"Auto-save error: {e}")

        self.matrix_view.refresh_table()
        self.preview_view.refresh_preview()

    def _on_tab_changed(self):
        curr_tab = self.tabview.get().strip()
        if curr_tab == self.tab_name_preview.strip():
            self.preview_view.refresh_preview()
        elif curr_tab == self.tab_name_matrix.strip():
            self.matrix_view.refresh_table()
        elif curr_tab == self.tab_name_drops.strip():
            self.logger_view.refresh_drops_list()

    def _handle_edit_metadata(self):
        def _on_save(updated_doc: ProtocolDocument):
            self.doc = updated_doc
            self.lbl_doc_title.configure(text=self.doc.title)
            self.lbl_doc_sub.configure(text=self._format_subtitle())
            self._on_document_changed()

        MetadataDialog(
            self,
            storage=self.storage,
            doc=self.doc,
            on_save=_on_save,
            is_new_doc=False,
        )

    def _handle_back(self):
        self.storage.save_document(self.doc)
        self.on_back_to_hub()

    def _set_status_message(self, msg: str):
        self.lbl_save_status.configure(text=f"● {msg}", text_color="#2b6cb0")
        self.after(3500, lambda: self.lbl_save_status.configure(text=t("status_saved"), text_color="#38a169"))
