"""
Adversarial Fact-Check Matrix View.
Displays all fact-check audits across the document and allows adding or editing claims
attached to specific drops or standalone literature audits.
Includes explicit field labels, drop selection, extended & custom verification statuses,
and external evidence file tags.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional, Dict, List

from models import ProtocolDocument, FactCheckEntry, InteractionDrop
from i18n import (
    t,
    get_localized_statuses,
    canonicalize_status,
    localize_status,
    localize_intent,
)
from gui.tooltip import create_tooltip


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
        self.editing_fc: Optional[FactCheckEntry] = None
        self.drop_options_map: Dict[str, Optional[str]] = {}

        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # 1. Header description
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

        # 2. Scrollable table container
        self.scroll_table = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        self.scroll_table.pack(fill="both", expand=True, padx=16, pady=4)

        # 3. Dedicated Fact-Check Form (Bottom)
        self.form_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray90", "gray17"))
        self.form_frame.pack(fill="x", padx=16, pady=(8, 12))

        header_form = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        header_form.pack(fill="x", padx=14, pady=(8, 2))

        self.lbl_form_mode = ctk.CTkLabel(
            header_form,
            text=t("fc_add_entry_title"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        )
        self.lbl_form_mode.pack(side="left")

        # Row 1: Drop Link & External Evidence File Checkbox
        row1 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(4, 2))
        row1.columnconfigure(0, weight=6)
        row1.columnconfigure(1, weight=4)

        # Drop Selector
        f_drop = ctk.CTkFrame(row1, fg_color="transparent")
        f_drop.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_drop, text=t("lbl_fc_link_drop"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self._update_drop_options()
        self.var_drop_select = ctk.StringVar(value=list(self.drop_options_map.keys())[0])
        self.combo_drop = ctk.CTkComboBox(
            f_drop,
            values=list(self.drop_options_map.keys()),
            variable=self.var_drop_select,
            height=30,
        )
        self.combo_drop.pack(fill="x", pady=(2, 0))

        # External File Checkbox
        f_file = ctk.CTkFrame(row1, fg_color="transparent")
        f_file.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(f_file, text="", font=ctk.CTkFont(size=11)).pack(anchor="w")  # alignment spacer
        self.var_is_file = ctk.BooleanVar(value=False)
        self.cb_is_file = ctk.CTkCheckBox(
            f_file,
            text=t("lbl_fc_is_file"),
            variable=self.var_is_file,
            font=ctk.CTkFont(size=11),
            height=26,
            checkbox_width=18,
            checkbox_height=18,
        )
        self.cb_is_file.pack(anchor="w", pady=(4, 0))
        create_tooltip(self.cb_is_file, t("tooltip_fc_is_file"))

        # Row 2: Extracted Claim & Source Citation with explicit labels
        row2 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=4)
        row2.columnconfigure(0, weight=6)
        row2.columnconfigure(1, weight=4)

        # Claim
        f_claim = ctk.CTkFrame(row2, fg_color="transparent")
        f_claim.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_claim, text=t("lbl_fc_claim"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.var_claim = ctk.StringVar()
        self.entry_claim = ctk.CTkEntry(
            f_claim,
            textvariable=self.var_claim,
            placeholder_text=t("ph_fc_claim"),
            height=30,
        )
        self.entry_claim.pack(fill="x", pady=(2, 0))

        # Source
        f_src = ctk.CTkFrame(row2, fg_color="transparent")
        f_src.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(f_src, text=t("lbl_fc_source"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.var_source = ctk.StringVar()
        self.entry_source = ctk.CTkEntry(
            f_src,
            textvariable=self.var_source,
            placeholder_text=t("ph_fc_source"),
            height=30,
        )
        self.entry_source.pack(fill="x", pady=(2, 0))

        # Row 3: Status & Audit Note & Action Buttons
        row3 = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        row3.pack(fill="x", padx=14, pady=(4, 10))
        row3.columnconfigure(0, weight=3)
        row3.columnconfigure(1, weight=5)
        row3.columnconfigure(2, weight=2)

        # Status Combobox (Allows presets OR free typing)
        f_status = ctk.CTkFrame(row3, fg_color="transparent")
        f_status.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_status, text=t("lbl_fc_status"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        localized_statuses = get_localized_statuses()
        self.var_status = ctk.StringVar(value=localized_statuses[0])
        self.combo_status = ctk.CTkComboBox(
            f_status,
            values=localized_statuses,
            variable=self.var_status,
            height=30,
        )
        self.combo_status.pack(fill="x", pady=(2, 0))

        # Rectification Note
        f_note = ctk.CTkFrame(row3, fg_color="transparent")
        f_note.grid(row=0, column=1, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(f_note, text=t("lbl_fc_note"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.var_note = ctk.StringVar()
        self.entry_note = ctk.CTkEntry(
            f_note,
            textvariable=self.var_note,
            placeholder_text=t("ph_fc_note"),
            height=30,
        )
        self.entry_note.pack(fill="x", pady=(2, 0))

        # Action Buttons Box
        f_actions = ctk.CTkFrame(row3, fg_color="transparent")
        f_actions.grid(row=0, column=2, sticky="sew")
        ctk.CTkLabel(f_actions, text="", font=ctk.CTkFont(size=11)).pack(anchor="w")  # alignment spacer

        f_btn_inner = ctk.CTkFrame(f_actions, fg_color="transparent")
        f_btn_inner.pack(fill="x", pady=(2, 0))

        self.btn_submit = ctk.CTkButton(
            f_btn_inner,
            text=t("btn_add_entry"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=30,
            command=self._handle_submit,
        )
        self.btn_submit.pack(side="left", fill="x", expand=True)

        self.btn_cancel = ctk.CTkButton(
            f_btn_inner,
            text=t("btn_cancel_edit_fc"),
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            height=30,
            width=80,
            command=self._reset_form,
        )
        # Hidden by default in Add mode
        self.btn_cancel.pack_forget()

        # Keyboard shortcuts: Escape to cancel edit, Ctrl+Return to submit
        for widget in (self.entry_claim, self.entry_source, self.entry_note):
            widget.bind("<Escape>", lambda e: self._reset_form())
            widget.bind("<Control-Return>", lambda e: self._handle_submit())

    def _update_drop_options(self):
        """Populates the Drop selector mapping from active document drops."""
        self.drop_options_map = {
            t("opt_standalone_drop"): None
        }
        self.doc.renumber_drops()
        for d in self.doc.drops:
            loc_intent = localize_intent(d.core_intent)
            if d.title and d.title.strip():
                label = f"Interaction #{d.drop_number}: {d.title.strip()} [{loc_intent}] ({d.target_engine})"
            else:
                label = f"Interaction #{d.drop_number}: {loc_intent} ({d.target_engine})"
            self.drop_options_map[label] = d.id

    def refresh_table(self):
        """Renders all fact-check entries across drops and standalone items."""
        for widget in self.scroll_table.winfo_children():
            widget.destroy()

        self._update_drop_options()
        if hasattr(self, "combo_drop"):
            self.combo_drop.configure(values=list(self.drop_options_map.keys()))

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
        tbl_hdr.columnconfigure(0, weight=2)  # Origin
        tbl_hdr.columnconfigure(1, weight=4)  # Claim
        tbl_hdr.columnconfigure(2, weight=3)  # Source
        tbl_hdr.columnconfigure(3, weight=2)  # Status
        tbl_hdr.columnconfigure(4, weight=3)  # Note
        tbl_hdr.columnconfigure(5, weight=1, minsize=130)  # Actions

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
        is_editing_this = bool(self.editing_fc and self.editing_fc.id == fc.id)
        bg_row = ("#ebf8ff", "#1a365d") if is_editing_this else ("white", "gray19")
        border_col = ("#3182ce", "#63b3ed") if is_editing_this else ("gray85", "gray28")

        row = ctk.CTkFrame(
            self.scroll_table,
            fg_color=bg_row,
            corner_radius=6,
            border_width=2 if is_editing_this else 1,
            border_color=border_col,
            cursor="hand2",
        )
        row.pack(fill="x", pady=2, padx=2)
        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=4)
        row.columnconfigure(2, weight=3)
        row.columnconfigure(3, weight=2)
        row.columnconfigure(4, weight=3)
        row.columnconfigure(5, weight=1, minsize=130)

        create_tooltip(row, t("tooltip_click_edit_fc"))
        on_edit_click = lambda e, entry=fc: self._load_entry_into_form(entry)
        row.bind("<Double-Button-1>", on_edit_click)

        # 1. Ref / Origin & Interaction Short Title
        ref_text = fc.drop_reference or "General"
        target_drop = next((d for d in self.doc.drops if d.id == fc.drop_id), None) if fc.drop_id else None

        f_ref_cell = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
        f_ref_cell.grid(row=0, column=0, padx=6, pady=6, sticky="w")
        f_ref_cell.bind("<Double-Button-1>", on_edit_click)

        lbl_ref = ctk.CTkLabel(f_ref_cell, text=ref_text, font=ctk.CTkFont(size=11, weight="bold"), cursor="hand2")
        lbl_ref.pack(anchor="w")
        lbl_ref.bind("<Double-Button-1>", on_edit_click)

        if target_drop and target_drop.title and target_drop.title.strip():
            title_text = target_drop.title.strip()
            if len(title_text) > 30:
                title_text = title_text[:28] + "..."
            lbl_title = ctk.CTkLabel(
                f_ref_cell,
                text=title_text,
                font=ctk.CTkFont(size=9),
                text_color=("gray40", "gray60"),
                cursor="hand2",
            )
            lbl_title.pack(anchor="w", pady=(1, 0))
            lbl_title.bind("<Double-Button-1>", on_edit_click)

        # 2. Claim
        lbl_claim = ctk.CTkLabel(row, text=fc.claim, font=ctk.CTkFont(size=11), wraplength=260, justify="left", cursor="hand2")
        lbl_claim.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        lbl_claim.bind("<Double-Button-1>", on_edit_click)

        # 3. Source & External File Badge
        f_src_cell = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
        f_src_cell.grid(row=0, column=2, padx=6, pady=6, sticky="w")
        f_src_cell.bind("<Double-Button-1>", on_edit_click)

        if fc.is_external_file:
            lbl_file_tag = ctk.CTkLabel(
                f_src_cell,
                text=t("badge_file_evidence"),
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=("gray85", "gray30"),
                text_color=("gray20", "gray90"),
                corner_radius=4,
                padx=4,
                pady=1,
            )
            lbl_file_tag.pack(anchor="w", pady=(0, 2))
            lbl_file_tag.bind("<Double-Button-1>", on_edit_click)

        src_text = fc.primary_source or "—"
        lbl_src = ctk.CTkLabel(f_src_cell, text=src_text, font=ctk.CTkFont(size=11), wraplength=200, justify="left", text_color=("gray30", "gray70"), cursor="hand2")
        lbl_src.pack(anchor="w")
        lbl_src.bind("<Double-Button-1>", on_edit_click)

        # 4. Status Badge
        color_map = {
            "Confirmed": ("#c6f6d5", "#22543d"),
            "Refuted": ("#fed7d7", "#742a2a"),
            "Clarified": ("#bee3f8", "#2b6cb0"),
            "Disputed": ("#e9d8fd", "#553c9a"),
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
            cursor="hand2",
        )
        lbl_stat.grid(row=0, column=3, padx=6, pady=6, sticky="w")
        lbl_stat.bind("<Double-Button-1>", on_edit_click)

        # 5. Note
        lbl_note = ctk.CTkLabel(row, text=fc.rectification_note or "—", font=ctk.CTkFont(size=11), wraplength=180, justify="left", cursor="hand2")
        lbl_note.grid(row=0, column=4, padx=6, pady=6, sticky="w")
        lbl_note.bind("<Double-Button-1>", on_edit_click)

        # 6. Action Buttons (Edit + Delete)
        f_acts = ctk.CTkFrame(row, fg_color="transparent")
        f_acts.grid(row=0, column=5, padx=6, pady=6, sticky="e")

        btn_edit = ctk.CTkButton(
            f_acts,
            text=t("btn_edit"),
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            command=lambda entry=fc: self._load_entry_into_form(entry),
        )
        btn_edit.pack(side="left", padx=(0, 4))
        create_tooltip(btn_edit, t("tooltip_click_edit_fc"))

        btn_del = ctk.CTkButton(
            f_acts,
            text=t("btn_delete"),
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#e53e3e", "#fc8181"),
            hover_color=("gray90", "gray28"),
            border_width=1,
            command=lambda entry=fc: self._delete_entry(entry),
        )
        btn_del.pack(side="left")

    def _load_entry_into_form(self, entry: FactCheckEntry):
        """Loads an existing fact check into the form for editing."""
        self.editing_fc = entry
        ref_text = entry.drop_reference or "Standalone"
        self.lbl_form_mode.configure(text=f"{t('fc_edit_entry_title')} ({ref_text})")
        self.btn_submit.configure(text=t("btn_update_entry"))
        self.btn_cancel.pack(side="left", padx=(6, 0))

        # Select corresponding drop in dropdown
        target_label = t("opt_standalone_drop")
        for label, d_id in self.drop_options_map.items():
            if d_id and entry.drop_id == d_id:
                target_label = label
                break
        self.var_drop_select.set(target_label)

        self.var_claim.set(entry.claim)
        self.var_source.set(entry.primary_source)
        self.var_is_file.set(entry.is_external_file)
        self.var_status.set(localize_status(entry.status))
        self.var_note.set(entry.rectification_note)

        # Autofocus claim input for instant keyboard editing
        if hasattr(self, "entry_claim"):
            self.after(50, lambda: self.entry_claim.focus_set())

        self.refresh_table()

    def _reset_form(self):
        """Resets the form back to Add mode."""
        self.editing_fc = None
        self.lbl_form_mode.configure(text=t("fc_add_entry_title"))
        self.btn_submit.configure(text=t("btn_add_entry"))
        self.btn_cancel.pack_forget()

        self.var_drop_select.set(list(self.drop_options_map.keys())[0])
        self.var_claim.set("")
        self.var_source.set("")
        self.var_is_file.set(False)
        localized_statuses = get_localized_statuses()
        self.var_status.set(localized_statuses[0])
        self.var_note.set("")

        self.refresh_table()

    def _handle_submit(self):
        claim = self.var_claim.get().strip()
        if not claim:
            messagebox.showwarning("Validation", t("val_claim_required"))
            return

        source = self.var_source.get().strip()
        raw_status = self.var_status.get().strip() or "Confirmed"
        canonical_stat = canonicalize_status(raw_status)
        note = self.var_note.get().strip()
        is_file = self.var_is_file.get()
        selected_drop_id = self.drop_options_map.get(self.var_drop_select.get())

        if self.editing_fc:
            # Update existing entry
            self.editing_fc.claim = claim
            self.editing_fc.primary_source = source
            self.editing_fc.status = canonical_stat
            self.editing_fc.rectification_note = note
            self.editing_fc.is_external_file = is_file
            self.doc.assign_fact_check(self.editing_fc, selected_drop_id)
        else:
            # Create new entry
            new_fc = FactCheckEntry(
                claim=claim,
                primary_source=source,
                status=canonical_stat,
                rectification_note=note,
                is_external_file=is_file,
            )
            self.doc.assign_fact_check(new_fc, selected_drop_id)

        self._reset_form()
        self.on_document_changed()

    def _delete_entry(self, entry: FactCheckEntry):
        confirm = messagebox.askyesno(
            t("confirm_delete_title"),
            t("confirm_delete_msg", item=f'"{entry.claim[:40]}..."'),
        )
        if confirm:
            if self.editing_fc and self.editing_fc.id == entry.id:
                self._reset_form()

            if entry in self.doc.standalone_fact_checks:
                self.doc.standalone_fact_checks.remove(entry)
            else:
                for drop in self.doc.drops:
                    if entry in drop.fact_checks:
                        drop.fact_checks.remove(entry)
                        break

            self.refresh_table()
            self.on_document_changed()

    def _handle_add_standalone(self):
        """Backward-compatible alias for _handle_submit."""
        self._handle_submit()

