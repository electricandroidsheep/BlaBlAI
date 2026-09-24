"""
Focused Assignment Metadata Modal Dialog.
Handles assignment-specific attributes (Title, Course, Scope, Examiner, Submission Date)
and safeguards author provenance with an External Author read-only lock.
"""

from __future__ import annotations
import customtkinter as ctk
from typing import Optional, Callable
from models import ProtocolDocument, ProtocolMetadata, get_current_date
from storage import StorageManager
from i18n import t
from gui.tooltip import create_tooltip


class MetadataDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        storage: StorageManager,
        doc: Optional[ProtocolDocument] = None,
        on_save: Optional[Callable[[ProtocolDocument], None]] = None,
        is_new_doc: bool = False,
    ):
        super().__init__(parent)
        self.storage = storage
        self.doc = doc
        self.on_save = on_save
        self.is_new_doc = is_new_doc

        title_key = "meta_dialog_title_new" if is_new_doc else "meta_dialog_title_edit"
        self.title(t(title_key))
        self.geometry("600x640")
        self.minsize(520, 520)
        self.grab_set()

        self._build_ui()
        self._populate_fields()

        self.after(50, self._center_window)

    def _center_window(self):
        self.update_idletasks()
        try:
            parent_x = self.master.winfo_x()
            parent_y = self.master.winfo_y()
            parent_w = self.master.winfo_width()
            parent_h = self.master.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = parent_x + (parent_w - w) // 2
            y = parent_y + (parent_h - h) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=(16, 12))

        # Header Title
        lbl_title = ctk.CTkLabel(
            scroll,
            text=t("meta_heading"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        lbl_title.pack(anchor="w", pady=(0, 2))

        lbl_desc = ctk.CTkLabel(
            scroll,
            text="Assignment, course, and author provenance metadata.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        lbl_desc.pack(anchor="w", pady=(0, 12))

        # Document Title
        default_title = self.storage.generate_default_document_title() if self.is_new_doc else (self.doc.title if self.doc else "")
        self.var_doc_title = ctk.StringVar(value=default_title)
        entry_title = self._add_labeled_entry(scroll, t("lbl_doc_title"), self.var_doc_title, placeholder="e.g. Master's Thesis AI Protocol")
        create_tooltip(entry_title, t("tooltip_new_doc_title"))

        # Course Code & Title
        self.var_course = ctk.StringVar()
        entry_course = self._add_labeled_entry(scroll, t("lbl_course_code"), self.var_course, placeholder="e.g. DBM-501: Master Thesis Research")
        create_tooltip(entry_course, t("tooltip_new_doc_course"))

        # Assignment Scope - Free text entry
        self.var_scope = ctk.StringVar(value="Master's Thesis")
        entry_scope = self._add_labeled_entry(scroll, t("lbl_assignment_scope"), self.var_scope, placeholder="e.g. Master's Thesis, Seminar Paper, Case Study, Project")
        create_tooltip(entry_scope, t("tooltip_new_doc_scope"))

        # Examiner / Supervisor
        self.var_examiner = ctk.StringVar()
        entry_examiner = self._add_labeled_entry(scroll, t("lbl_examiner"), self.var_examiner, placeholder="e.g. Prof. Dr. Barbara Krumay")
        create_tooltip(entry_examiner, t("tooltip_new_doc_examiner"))

        # Submission Date
        self.var_date = ctk.StringVar(value=get_current_date())
        entry_date = self._add_labeled_entry(scroll, t("lbl_submission_date"), self.var_date, placeholder="YYYY-MM-DD")

        # Author info section & Read-only external author guard
        self.frame_author_header = ctk.CTkFrame(scroll, fg_color="transparent")
        self.frame_author_header.pack(fill="x", pady=(12, 4))

        ctk.CTkLabel(
            self.frame_author_header,
            text="Author Academic Identity",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        ).pack(side="left")

        # External author detection banner
        self.banner_external = ctk.CTkFrame(scroll, corner_radius=6, fg_color=("#fed7d7", "#742a2a"))
        self.lbl_ext_author = ctk.CTkLabel(
            self.banner_external,
            text=t("lbl_external_author"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#742a2a", "#feb2b2"),
        )
        self.lbl_ext_author.pack(side="left", padx=8, pady=4)

        self.btn_unlock_author = ctk.CTkButton(
            self.banner_external,
            text=t("btn_unlock_author"),
            width=140,
            height=24,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("white", "gray20"),
            text_color=("gray10", "white"),
            command=self._unlock_author_fields,
        )
        self.btn_unlock_author.pack(side="right", padx=6, pady=4)

        self.var_student_name = ctk.StringVar()
        self.entry_name = self._add_labeled_entry(scroll, t("lbl_student_name"), self.var_student_name, placeholder="Sven Várszegi, B.A.")
        create_tooltip(self.entry_name, t("tooltip_profile_name"))

        self.var_degree = ctk.StringVar()
        self.entry_degree = self._add_labeled_entry(scroll, t("lbl_degree_program"), self.var_degree, placeholder="Master Digital Business Management (FH OÖ / JKU)")
        create_tooltip(self.entry_degree, t("tooltip_profile_degree"))

        self.var_matrikel = ctk.StringVar()
        self.entry_matrikel = self._add_labeled_entry(scroll, t("lbl_matriculation"), self.var_matrikel, placeholder="e.g. k12345678 or 2210283001")
        create_tooltip(self.entry_matrikel, t("tooltip_profile_matriculation"))

        # Bottom Button Bar
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        btn_cancel = ctk.CTkButton(
            btn_bar,
            text=t("btn_cancel"),
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy,
            width=100,
        )
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_save_text = t("btn_create_doc") if self.is_new_doc else t("btn_save")
        btn_save = ctk.CTkButton(
            btn_bar,
            text=btn_save_text,
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            command=self._handle_save,
            width=140,
        )
        btn_save.pack(side="right")

    def _add_labeled_entry(self, parent, label_text: str, variable: ctk.StringVar, placeholder: str = ""):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(6, 2))
        entry = ctk.CTkEntry(parent, textvariable=variable, placeholder_text=placeholder, width=380, height=30)
        entry.pack(anchor="w", pady=(0, 4), fill="x")
        return entry

    def _unlock_author_fields(self):
        self.entry_name.configure(state="normal")
        self.entry_degree.configure(state="normal")
        self.entry_matrikel.configure(state="normal")
        self.banner_external.pack_forget()

    def _populate_fields(self):
        if self.doc:
            m = self.doc.metadata
            self.var_doc_title.set(self.doc.title)
            self.var_student_name.set(m.student_name)
            self.var_degree.set(m.degree_program)
            self.var_matrikel.set(m.matriculation_number)
            self.var_course.set(m.course_code_title)
            self.var_scope.set(m.assignment_scope)
            self.var_examiner.set(m.examiner)
            self.var_date.set(m.submission_date)

            is_external = bool(
                not self.is_new_doc
                and m.student_name
                and m.student_name.strip() != self.storage.student_name.strip()
            )
            if is_external:
                self.banner_external.pack(fill="x", pady=(0, 6), before=self.entry_name)
                self.entry_name.configure(state="disabled")
                self.entry_degree.configure(state="disabled")
                self.entry_matrikel.configure(state="disabled")
            else:
                self.banner_external.pack_forget()
        else:
            self.var_student_name.set(self.storage.student_name)
            self.var_degree.set(self.storage.degree_program)
            self.var_matrikel.set(self.storage.matriculation_number)
            self.banner_external.pack_forget()

    def _handle_save(self):
        title = self.var_doc_title.get().strip() or "Academic AI Protocol"

        if self.is_new_doc or self.doc is None:
            doc = self.storage.create_new_document(
                title=title,
                course=self.var_course.get().strip(),
                assignment_scope=self.var_scope.get().strip(),
                examiner=self.var_examiner.get().strip(),
                save_immediately=False,
            )
        else:
            doc = self.doc
            doc.title = title

        doc.metadata.student_name = self.var_student_name.get().strip() or self.storage.student_name
        doc.metadata.degree_program = self.var_degree.get().strip() or self.storage.degree_program
        doc.metadata.matriculation_number = self.var_matrikel.get().strip()
        doc.metadata.course_code_title = self.var_course.get().strip()
        doc.metadata.assignment_scope = self.var_scope.get().strip()
        doc.metadata.examiner = self.var_examiner.get().strip()
        doc.metadata.submission_date = self.var_date.get().strip() or get_current_date()

        self.storage.save_document(doc)

        if self.on_save:
            self.on_save(doc)

        self.destroy()
