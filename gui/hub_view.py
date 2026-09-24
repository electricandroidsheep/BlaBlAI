"""
Google Docs-style Start Screen (Document Hub).
Displays recent assignments/protocols, allows creating new documents,
browsing external files, managing the active storage directory,
and toggling Dark/Light theme and English/German language.
"""

from __future__ import annotations
import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Callable, Optional, Dict, Any

from storage import StorageManager
from models import ProtocolDocument
from gui.metadata_dialog import MetadataDialog
from gui.profile_dialog import ProfileSettingsDialog
from gui.about_dialog import AboutHelpDialog
from gui.assets import get_blablai_ctk_image
from gui.tooltip import create_tooltip
from i18n import (
    t,
    get_current_locale,
    set_current_locale,
    add_locale_listener,
    remove_locale_listener,
)


class HubView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        storage: StorageManager,
        on_open_document: Callable[[ProtocolDocument], None],
        on_toggle_theme: Optional[Callable[[], None]] = None,
        on_language_changed: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.storage = storage
        self.on_open_document = on_open_document
        self.on_toggle_theme = on_toggle_theme
        self.on_language_changed = on_language_changed

        self._build_ui()
        self.refresh_documents()

        if not self.storage.onboarding_completed:
            self.after(350, lambda: self._open_profile_settings(is_onboarding=True))

    def _build_ui(self):
        # Clear any existing child widgets if rebuilding
        for w in self.winfo_children():
            w.destroy()

        # 1. Top Header Profile Bar
        header = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        header.pack(fill="x", padx=20, pady=(15, 10))

        # Title and branding on the left
        left_box = ctk.CTkFrame(header, fg_color="transparent")
        left_box.pack(side="left", padx=16, pady=12)

        self.brand_icon = get_blablai_ctk_image((36, 36))
        lbl_icon = ctk.CTkLabel(left_box, image=self.brand_icon, text="")
        lbl_icon.pack(side="left", padx=(0, 10))

        title_row = ctk.CTkFrame(left_box, fg_color="transparent")
        title_row.pack(side="left")

        lbl_app = ctk.CTkLabel(
            title_row,
            text=t("app_title"),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        lbl_app.pack(side="left")

        lbl_home_tag = ctk.CTkLabel(
            title_row,
            text=f" • {t('home_label')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray45", "gray55"),
        )
        lbl_home_tag.pack(side="left", padx=(6, 0))

        # Controls & Profile on the right
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right", padx=16, pady=12)

        # User Profile Button & Credential Badge
        btn_profile = ctk.CTkButton(
            right_box,
            text=f"👤 {t('user_profile')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray85", "gray22"),
            hover_color=("gray75", "gray28"),
            text_color=("gray10", "gray90"),
            border_width=1,
            height=32,
            command=self._open_profile_settings,
        )
        btn_profile.pack(side="left", padx=(0, 10))
        create_tooltip(btn_profile, t("tooltip_profile"))

        mat_info = f" [{self.storage.matriculation_number}]" if self.storage.matriculation_number else ""
        self.lbl_user = ctk.CTkLabel(
            right_box,
            text=f"{self.storage.student_name}{mat_info}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray65"),
        )
        self.lbl_user.pack(side="left", padx=(0, 12))

        # Language Toggle Button (EN / DE)
        curr_loc = get_current_locale().upper()
        btn_lang = ctk.CTkButton(
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
        btn_lang.pack(side="left", padx=(0, 6))
        create_tooltip(btn_lang, t("tooltip_lang"))

        if self.on_toggle_theme:
            btn_theme = ctk.CTkButton(
                right_box,
                text=t("btn_theme"),
                width=75,
                height=32,
                fg_color="transparent",
                border_width=1,
                text_color=("gray20", "gray80"),
                command=self.on_toggle_theme,
            )
            btn_theme.pack(side="left", padx=(0, 6))
            create_tooltip(btn_theme, t("tooltip_theme"))

        btn_about = ctk.CTkButton(
            right_box,
            text=t("btn_about"),
            width=115,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=("gray85", "gray22"),
            hover_color=("gray75", "gray28"),
            text_color=("gray10", "gray90"),
            border_width=1,
            command=self._open_about_dialog,
        )
        btn_about.pack(side="left")
        create_tooltip(btn_about, "Scholarly rationale, workflow instructions, and creator credits.")

        # 2. Storage Directory Bar
        storage_bar = ctk.CTkFrame(self, corner_radius=8, fg_color=("gray95", "gray15"))
        storage_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_folder = ctk.CTkLabel(
            storage_bar,
            text=t("hub_storage_folder", folder=str(self.storage.storage_dir)),
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
        )
        self.lbl_folder.pack(side="left", padx=14, pady=8)

        btn_open_folder = ctk.CTkButton(
            storage_bar,
            text=t("btn_open_explorer"),
            width=135,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            command=self._open_storage_folder,
        )
        btn_open_folder.pack(side="right", padx=(4, 10), pady=6)
        create_tooltip(btn_open_folder, "Open the active storage directory in your system file explorer.")

        btn_change_folder = ctk.CTkButton(
            storage_bar,
            text=t("btn_change_folder"),
            width=120,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            command=self._change_storage_folder,
        )
        btn_change_folder.pack(side="right", padx=4, pady=6)
        create_tooltip(btn_change_folder, "Select a new directory to store your .ailog files.")

        # 3. Actions Row
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=(4, 12))

        btn_new_doc = ctk.CTkButton(
            actions_frame,
            text=t("btn_new_document"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=38,
            width=160,
            command=self._handle_new_document,
        )
        btn_new_doc.pack(side="left", padx=(0, 10))
        create_tooltip(btn_new_doc, "Create a new AI interaction protocol document.")

        btn_open_ext = ctk.CTkButton(
            actions_frame,
            text=t("btn_open_external"),
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray95"),
            hover_color=("gray70", "gray35"),
            height=38,
            width=180,
            command=self._handle_open_external,
        )
        btn_open_ext.pack(side="left", padx=(0, 10))
        create_tooltip(btn_open_ext, "Open an existing .ailog file from anywhere on disk.")

        btn_refresh = ctk.CTkButton(
            actions_frame,
            text=f"↺ {t('btn_refresh')}",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=1,
            height=38,
            width=100,
            command=self.refresh_documents,
        )
        btn_refresh.pack(side="left")
        create_tooltip(btn_refresh, "Rescan the storage folder for updated files.")

        # 4. Documents List Header & Scroll Area
        list_header = ctk.CTkFrame(self, fg_color="transparent")
        list_header.pack(fill="x", padx=20, pady=(6, 4))

        self.lbl_list_title = ctk.CTkLabel(
            list_header,
            text=t("hub_recent_docs_title", count=0),
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.lbl_list_title.pack(side="left")

        self.scroll_docs = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        self.scroll_docs.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _open_profile_settings(self, is_onboarding: bool = False):
        def _on_save():
            mat_info = f" [{self.storage.matriculation_number}]" if self.storage.matriculation_number else ""
            self.lbl_user.configure(text=f"{self.storage.student_name}{mat_info}")
            self.refresh_documents()
        ProfileSettingsDialog(self, self.storage, on_save=_on_save, is_onboarding=is_onboarding)

    def _open_about_dialog(self):
        AboutHelpDialog(self)

    def _toggle_language(self):
        new_loc = "de" if get_current_locale() == "en" else "en"
        set_current_locale(new_loc)
        self.storage.ui_locale = new_loc
        self._build_ui()
        self.refresh_documents()
        if self.on_language_changed:
            self.on_language_changed(new_loc)

    def refresh_documents(self):
        """Scans storage folder and re-renders the document cards."""
        for widget in self.scroll_docs.winfo_children():
            widget.destroy()

        self.lbl_folder.configure(text=t("hub_storage_folder", folder=str(self.storage.storage_dir)))
        docs = self.storage.list_documents()
        self.lbl_list_title.configure(text=t("hub_recent_docs_title", count=len(docs)))

        if not docs:
            empty_box = ctk.CTkFrame(self.scroll_docs, fg_color="transparent")
            empty_box.pack(pady=60)

            ctk.CTkLabel(
                empty_box,
                text=t("hub_empty_title"),
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=("gray40", "gray60"),
            ).pack(pady=(0, 8))

            ctk.CTkLabel(
                empty_box,
                text=t("hub_empty_desc"),
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray50"),
            ).pack(pady=(0, 16))

            ctk.CTkButton(
                empty_box,
                text=t("btn_create_first"),
                fg_color=("#2b6cb0", "#3182ce"),
                command=self._handle_new_document,
            ).pack()
            return

        for doc_info in docs:
            self._create_document_card(doc_info)

    def _create_document_card(self, info: Dict[str, Any]):
        card = ctk.CTkFrame(
            self.scroll_docs,
            corner_radius=8,
            fg_color=("white", "gray19"),
            border_width=1,
            border_color=("gray85", "gray25"),
        )
        card.pack(fill="x", pady=6, padx=6)

        info_col = ctk.CTkFrame(card, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True, padx=14, pady=10)

        title_row = ctk.CTkFrame(info_col, fg_color="transparent")
        title_row.pack(fill="x")

        lbl_doc_title = ctk.CTkLabel(
            title_row,
            text=f"📄  {info['title']}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=("gray10", "gray95"),
        )
        lbl_doc_title.pack(side="left")

        # External author indicator badge
        author = info.get("student_name", "").strip()
        if author and author != self.storage.student_name.strip():
            ext_badge = ctk.CTkLabel(
                title_row,
                text="🔒 External Author",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("#fed7d7", "#742a2a"),
                text_color=("#742a2a", "#feb2b2"),
                corner_radius=4,
                padx=6,
                pady=1,
            )
            ext_badge.pack(side="left", padx=(8, 0))
            create_tooltip(ext_badge, f"Authored by {author}")

        lbl_meta = ctk.CTkLabel(
            info_col,
            text=t("card_course_scope", course=info['course'], scope=info['assignment_scope'] or "Assignment"),
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        lbl_meta.pack(anchor="w", pady=(2, 4))

        badges_row = ctk.CTkFrame(info_col, fg_color="transparent")
        badges_row.pack(anchor="w")

        drops_badge = ctk.CTkLabel(
            badges_row,
            text=t("card_drops_count", count=info['drops_count']),
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=("#e2e8f0", "#2d3748"),
            corner_radius=4,
            padx=8,
            pady=2,
        )
        drops_badge.pack(side="left", padx=(0, 8))

        time_badge = ctk.CTkLabel(
            badges_row,
            text=t("card_modified", time=info['last_modified']),
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray55"),
        )
        time_badge.pack(side="left")

        # Right Action Buttons
        actions_col = ctk.CTkFrame(card, fg_color="transparent")
        actions_col.pack(side="right", padx=14, pady=10)

        btn_open = ctk.CTkButton(
            actions_col,
            text=t("btn_open"),
            width=75,
            height=32,
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            command=lambda path=info["file_path"]: self._open_file(path),
        )
        btn_open.pack(side="left", padx=3)

        btn_edit_meta = ctk.CTkButton(
            actions_col,
            text="⚙",
            width=32,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            hover_color=("gray90", "gray28"),
            command=lambda path=info["file_path"]: self._edit_card_metadata(path),
        )
        btn_edit_meta.pack(side="left", padx=3)

        btn_delete = ctk.CTkButton(
            actions_col,
            text="🗑",
            width=32,
            height=32,
            fg_color="transparent",
            text_color=("#e53e3e", "#fc8181"),
            border_width=1,
            hover_color=("gray90", "gray28"),
            command=lambda path=info["file_path"], title=info["title"]: self._delete_file(path, title),
        )
        btn_delete.pack(side="left", padx=3)

    def _edit_card_metadata(self, path: str):
        try:
            doc = self.storage.load_document(path)
            MetadataDialog(
                self,
                storage=self.storage,
                doc=doc,
                on_save=lambda updated: self.refresh_documents(),
                is_new_doc=False,
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not load document for editing:\n{e}")

    def _open_file(self, path: str):
        try:
            doc = self.storage.load_document(path)
            self.on_open_document(doc)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open document:\n{e}")

    def _delete_file(self, path: str, title: str):
        confirm = messagebox.askyesno(
            t("confirm_delete_title"),
            t("confirm_delete_doc_msg", title=title),
        )
        if confirm:
            self.storage.delete_document(path)
            self.refresh_documents()

    def _handle_new_document(self):
        dialog = MetadataDialog(
            self,
            storage=self.storage,
            is_new_doc=True,
            on_save=lambda doc: self.on_open_document(doc),
        )

    def _handle_open_external(self):
        file_path = filedialog.askopenfilename(
            title=t("dialog_open_external_title"),
            filetypes=[("AI Protocol Files", "*.ailog"), ("All Files", "*.*")],
        )
        if file_path:
            self._open_file(file_path)

    def _change_storage_folder(self):
        new_dir = filedialog.askdirectory(
            title=t("dialog_change_folder_title"),
            initialdir=str(self.storage.storage_dir),
        )
        if new_dir:
            self.storage.storage_dir = new_dir
            self.refresh_documents()

    def _open_storage_folder(self):
        folder = str(self.storage.storage_dir)
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.Popen([opener, folder])
