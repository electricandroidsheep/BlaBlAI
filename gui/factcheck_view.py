"""
Adversarial Fact-Check Matrix View.
Displays all fact-check audits across the document and allows adding standalone checks.
Fully localized for English and German with canonical status storage.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional

from models import ProtocolDocument, FactCheckEntry
from i18n import (
    t,
    get_localized_statuses,
    canonicalize_status,
    localize_status,
)


class FactCheckView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        doc: ProtocolDocument,
        on_document_changed: Callable[[], None],
    ):
        super().__init__(parent, fg_color="transparent")
        self.doc = doc
        self.on_document_changed = on_document_changed

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # Header description
        header = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        header.pack(fill="x", padx=16, pady=(12, 8))

        lbl_title = ctk.CTkLabel(
            header,
            text=t("fc_view_title"),
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        lbl_title.pack(anchor="w", padx=14, pady=(10, 2))

        lbl_desc = ctk.CTkLabel(
            header,
            text=t("fc_view_desc"),
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        lbl_desc.pack(anchor="w", padx=14, pady=(0, 10))

        # Scrollable table container
        self.scroll_table = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        self.scroll_table.pack(fill="both", expand=True, padx=16, pady=4)

        # Bottom Add Standalone Form
        add_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        add_frame.pack(fill="x", padx=16, pady=(8, 12))

        ctk.CTkLabel(
            add_frame,
            text=t("fc_add_standalone_title"),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        ).pack(anchor="w", padx=14, pady=(8, 4))

        row1 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=2)
        row1.columnconfigure(0, weight=6)
        row1.columnconfigure(1, weight=4)

        self.var_claim = ctk.StringVar()
        ctk.CTkEntry(
            row1,
            textvariable=self.var_claim,
            placeholder_text=t("ph_fc_standalone_claim"),
            height=32,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.var_source = ctk.StringVar()
        ctk.CTkEntry(
            row1,
            textvariable=self.var_source,
            placeholder_text=t("ph_fc_standalone_source"),
            height=32,
        ).grid(row=0, column=1, sticky="nsew")

        row2 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(4, 10))
        row2.columnconfigure(0, weight=2)
        row2.columnconfigure(1, weight=6)
        row2.columnconfigure(2, weight=2)

        localized_statuses = get_localized_statuses()
        self.var_status = ctk.StringVar(value=localized_statuses[0])
        combo_status = ctk.CTkComboBox(
            row2,
            values=localized_statuses,
            variable=self.var_status,
            height=32,
        )
        combo_status.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.var_note = ctk.StringVar()
        ctk.CTkEntry(
            row2,
            textvariable=self.var_note,
            placeholder_text=t("ph_fc_standalone_note"),
            height=32,
        ).grid(row=0, column=1, sticky="nsew", padx=(0, 6))

        btn_add = ctk.CTkButton(
            row2,
            text=t("btn_add_entry"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=32,
            command=self._handle_add_standalone,
        )
        btn_add.grid(row=0, column=2, sticky="nsew")

    def refresh_table(self):
        """Renders all fact-check entries in the matrix."""
        for widget in self.scroll_table.winfo_children():
            widget.destroy()

        all_checks = self.doc.get_all_fact_checks()

        if not all_checks:
            lbl_empty = ctk.CTkLabel(
                self.scroll_table,
                text=t("fc_empty"),
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray50"),
                justify="center",
            )
            lbl_empty.pack(pady=40)
            return

        # Table Header
        tbl_hdr = ctk.CTkFrame(self.scroll_table, fg_color=("gray85", "gray22"), corner_radius=6)
        tbl_hdr.pack(fill="x", pady=(0, 4), padx=2)
        tbl_hdr.columnconfigure(0, weight=1)  # Ref
        tbl_hdr.columnconfigure(1, weight=4)  # Claim
        tbl_hdr.columnconfigure(2, weight=3)  # Source
        tbl_hdr.columnconfigure(3, weight=2)  # Status
        tbl_hdr.columnconfigure(4, weight=3)  # Note
        tbl_hdr.columnconfigure(5, weight=1)  # Action

        ctk.CTkLabel(tbl_hdr, text=t("fc_th_origin"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(tbl_hdr, text=t("fc_th_claim"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(tbl_hdr, text=t("fc_th_source"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(tbl_hdr, text=t("fc_th_status"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(tbl_hdr, text=t("fc_th_note"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, padx=6, pady=4, sticky="w")
        ctk.CTkLabel(tbl_hdr, text=t("fc_th_action"), font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=5, padx=6, pady=4, sticky="e")

        # Table Rows
        for fc in all_checks:
            self._render_row(fc)

    def _render_row(self, fc: FactCheckEntry):
        row = ctk.CTkFrame(self.scroll_table, fg_color=("white", "gray19"), corner_radius=6)
        row.pack(fill="x", pady=2, padx=2)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=4)
        row.columnconfigure(2, weight=3)
        row.columnconfigure(3, weight=2)
        row.columnconfigure(4, weight=3)
        row.columnconfigure(5, weight=1)

        # Ref
        ref_text = fc.drop_reference or "General"
        ctk.CTkLabel(row, text=ref_text, font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=6, pady=6, sticky="w")

        # Claim
        lbl_claim = ctk.CTkLabel(row, text=fc.claim, font=ctk.CTkFont(size=11), wraplength=280, justify="left")
        lbl_claim.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        # Source
        lbl_src = ctk.CTkLabel(row, text=fc.primary_source or "—", font=ctk.CTkFont(size=11), wraplength=200, justify="left", text_color=("gray30", "gray70"))
        lbl_src.grid(row=0, column=2, padx=6, pady=6, sticky="w")

        # Status Badge
        color_map = {
            "Confirmed": ("#c6f6d5", "#22543d"),
            "Refuted": ("#fed7d7", "#742a2a"),
            "Untestable": ("#fefcbf", "#744210"),
        }
        bg_col, txt_col = color_map.get(fc.status, ("#edf2f7", "#4a5568"))
        loc_stat = localize_status(fc.status)
        lbl_stat = ctk.CTkLabel(
            row,
            text=f"[{loc_stat}]",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=bg_col,
            text_color=txt_col,
            corner_radius=4,
            padx=6,
            pady=1,
        )
        lbl_stat.grid(row=0, column=3, padx=6, pady=6, sticky="w")

        # Note
        lbl_note = ctk.CTkLabel(row, text=fc.rectification_note or "—", font=ctk.CTkFont(size=11), wraplength=180, justify="left")
        lbl_note.grid(row=0, column=4, padx=6, pady=6, sticky="w")

        # Delete Action (FIXED: Safe hex colors "#e53e3e", "#fc8181" instead of invalid "red600", "red400")
        btn_del = ctk.CTkButton(
            row,
            text="✕",
            width=28,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#e53e3e", "#fc8181"),
            hover_color=("gray90", "gray28"),
            border_width=1,
            command=lambda entry=fc: self._delete_entry(entry),
        )
        btn_del.grid(row=0, column=5, padx=6, pady=6, sticky="e")

    def _handle_add_standalone(self):
        claim = self.var_claim.get().strip()
        if not claim:
            messagebox.showwarning("Validation", t("val_claim_required"))
            return

        canonical_stat = canonicalize_status(self.var_status.get())
        fc = FactCheckEntry(
            claim=claim,
            primary_source=self.var_source.get().strip(),
            status=canonical_stat,
            rectification_note=self.var_note.get().strip(),
            drop_reference="Standalone",
        )
        self.doc.standalone_fact_checks.append(fc)

        # Clear inputs
        self.var_claim.set("")
        self.var_source.set("")
        self.var_note.set("")

        self.refresh_table()
        self.on_document_changed()

    def _delete_entry(self, entry: FactCheckEntry):
        if entry in self.doc.standalone_fact_checks:
            self.doc.standalone_fact_checks.remove(entry)
        else:
            for drop in self.doc.drops:
                if entry in drop.fact_checks:
                    drop.fact_checks.remove(entry)
                    break

        self.refresh_table()
        self.on_document_changed()
