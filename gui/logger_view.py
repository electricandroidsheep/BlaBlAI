"""
Interaction Drop Logger View.
Provides prompt/output entry form with two independent guided evaluation sections:
1. Critical Reflection & Plausibility Audit
2. Primary Source Fact-Checking
Features wizard-style explanatory sub-hints, gentle validation, and active session cards.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Optional, Callable, Dict, Any, List

from models import (
    ProtocolDocument,
    InteractionDrop,
    CriticalExamination,
    FactCheckEntry,
    get_current_cest_time,
)
from storage import StorageManager
from generator import clean_raw_interaction_text
from i18n import (
    t,
    get_localized_intents,
    canonicalize_intent,
    localize_intent,
    get_localized_decisions,
    canonicalize_decision,
    localize_decision,
    get_localized_statuses,
    canonicalize_status,
    localize_status,
)
from gui.tooltip import create_tooltip

ENGINE_OPTIONS = [
    "Anthropic Claude",
    "Google Gemini",
    "Google NotebookLM",
    "OpenAI ChatGPT",
    "Perplexity AI",
    "DeepSeek",
    "Meta Llama",
    "Custom...",
]


class LoggerView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        doc: ProtocolDocument,
        storage: Optional[StorageManager] = None,
        on_document_changed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.doc = doc
        self.storage = storage or StorageManager()
        self.on_document_changed = on_document_changed or (lambda: None)
        self.editing_drop_id: Optional[str] = None

        self._build_ui()
        self.refresh_drops_list()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        self.grid_columnconfigure(0, weight=6, minsize=460)
        self.grid_columnconfigure(1, weight=4, minsize=340)
        self.grid_rowconfigure(0, weight=1)

        # ----------------- LEFT: Input Form -----------------
        form_scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        form_scroll.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=10)

        # Form Header
        self.lbl_form_header = ctk.CTkLabel(
            form_scroll,
            text=t("log_heading_new"),
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        self.lbl_form_header.pack(anchor="w", pady=(2, 10))

        # Row 1: Timestamp & Engine
        row1 = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row1.pack(fill="x", pady=2)
        row1.columnconfigure(0, weight=5)
        row1.columnconfigure(1, weight=5)

        # Timestamp
        f_time = ctk.CTkFrame(row1, fg_color="transparent")
        f_time.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(f_time, text=t("lbl_timestamp"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        f_time_input = ctk.CTkFrame(f_time, fg_color="transparent")
        f_time_input.pack(fill="x")
        self.var_timestamp = ctk.StringVar(value=get_current_cest_time())
        self.entry_timestamp = ctk.CTkEntry(f_time_input, textvariable=self.var_timestamp, height=32)
        self.entry_timestamp.pack(side="left", fill="x", expand=True, padx=(0, 4))
        btn_refresh_time = ctk.CTkButton(
            f_time_input,
            text=t("btn_now"),
            width=55,
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            command=self._refresh_timestamp,
        )
        btn_refresh_time.pack(side="right")

        # Target Engine
        f_engine = ctk.CTkFrame(row1, fg_color="transparent")
        f_engine.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(f_engine, text=t("lbl_engine"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.var_engine = ctk.StringVar(value=self.storage.last_used_engine)
        self.combo_engine = ctk.CTkComboBox(f_engine, values=ENGINE_OPTIONS, variable=self.var_engine, height=32)
        self.combo_engine.pack(fill="x")

        # Row 2: Core Intent & Context Scope
        row2 = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row2.pack(fill="x", pady=6)
        row2.columnconfigure(0, weight=5)
        row2.columnconfigure(1, weight=5)

        # Core Intent
        f_intent = ctk.CTkFrame(row2, fg_color="transparent")
        f_intent.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(f_intent, text=t("lbl_intent"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        localized_intents = get_localized_intents()
        self.var_intent = ctk.StringVar(value=localized_intents[0])
        self.combo_intent = ctk.CTkComboBox(f_intent, values=localized_intents, variable=self.var_intent, height=32)
        self.combo_intent.pack(fill="x")

        # Context Scope
        f_scope = ctk.CTkFrame(row2, fg_color="transparent")
        f_scope.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(f_scope, text=t("lbl_context_scope"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.var_scope = ctk.StringVar(value="")
        self.entry_scope = ctk.CTkEntry(
            f_scope,
            textvariable=self.var_scope,
            placeholder_text=t("ph_context_scope"),
            height=32,
        )
        self.entry_scope.pack(fill="x")

        # Raw Prompt - Styled with Cool Blue Border #3182ce
        ctk.CTkLabel(
            form_scroll,
            text=t("lbl_raw_prompt"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", pady=(8, 2))
        self.txt_prompt = ctk.CTkTextbox(
            form_scroll,
            height=105,
            font=ctk.CTkFont(family="Consolas", size=12),
            border_width=2,
            border_color="#3182ce",
        )
        self.txt_prompt.pack(fill="x", pady=(0, 6))

        # Raw Output - Styled with Slate/Teal Border #38a169
        output_header = ctk.CTkFrame(form_scroll, fg_color="transparent")
        output_header.pack(fill="x", pady=(4, 2))

        ctk.CTkLabel(
            output_header,
            text=t("lbl_raw_output"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        # Non-blocking feedback toast for paste & tidy
        self.lbl_toast = ctk.CTkLabel(
            output_header,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        )
        self.lbl_toast.pack(side="left", padx=10)

        btn_tidy = ctk.CTkButton(
            output_header,
            text=t("btn_tidy_text"),
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            height=24,
            width=115,
            command=self._tidy_output_text,
        )
        btn_tidy.pack(side="right")
        create_tooltip(btn_tidy, t("tooltip_tidy_text"))

        self.txt_output = ctk.CTkTextbox(
            form_scroll,
            height=115,
            font=ctk.CTkFont(family="Consolas", size=12),
            border_width=2,
            border_color="#38a169",
        )
        self.txt_output.pack(fill="x", pady=(0, 6))
        self.txt_output.bind("<Control-v>", lambda e: self.after(50, self._on_output_paste))
        self.txt_output.bind("<Command-v>", lambda e: self.after(50, self._on_output_paste))

        # Generated Artifact / File Reference Field (e.g. video.mp4, chart.png)
        f_fileref = ctk.CTkFrame(form_scroll, fg_color="transparent")
        f_fileref.pack(fill="x", pady=(2, 8))
        ctk.CTkLabel(
            f_fileref,
            text=f"📎 {t('lbl_file_reference')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray25", "gray75"),
        ).pack(anchor="w", pady=(0, 2))
        self.var_file_ref = ctk.StringVar(value="")
        self.entry_file_ref = ctk.CTkEntry(
            f_fileref,
            textvariable=self.var_file_ref,
            placeholder_text=t("ph_file_reference"),
            height=32,
        )
        self.entry_file_ref.pack(fill="x")
        create_tooltip(self.entry_file_ref, t("tooltip_file_reference"))

        # ----------------- TOGGLES & EXPANDABLE EVALUATION SECTIONS -----------------
        # Container 1: Critical Reflection & Plausibility
        self.container_critical = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.container_critical.pack(fill="x", pady=(4, 0))

        self.var_enable_critical = ctk.BooleanVar(value=False)
        self.switch_critical = ctk.CTkSwitch(
            self.container_critical,
            text=t("switch_critical"),
            variable=self.var_enable_critical,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_critical_frame,
        )
        self.switch_critical.pack(anchor="w", pady=(2, 4))

        self.frame_critical = ctk.CTkFrame(self.container_critical, corner_radius=8, fg_color=("gray90", "gray18"))
        self._build_critical_frame(self.frame_critical)

        # Container 2: Primary Source Fact-Check
        self.container_factcheck = ctk.CTkFrame(form_scroll, fg_color="transparent")
        self.container_factcheck.pack(fill="x", pady=(4, 0))

        self.var_enable_factcheck = ctk.BooleanVar(value=False)
        self.switch_factcheck = ctk.CTkSwitch(
            self.container_factcheck,
            text=t("switch_fact_check"),
            variable=self.var_enable_factcheck,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._toggle_factcheck_frame,
        )
        self.switch_factcheck.pack(anchor="w", pady=(2, 4))

        self.frame_factcheck = ctk.CTkFrame(self.container_factcheck, corner_radius=8, fg_color=("gray90", "gray18"))
        self._build_factcheck_frame(self.frame_factcheck)

        # Continuous Autosave Banner
        banner_autosave = ctk.CTkFrame(form_scroll, fg_color=("gray90", "gray20"), corner_radius=6)
        banner_autosave.pack(fill="x", pady=(10, 4), ipadx=8, ipady=4)
        ctk.CTkLabel(
            banner_autosave,
            text=t("lbl_autosave_banner"),
            font=ctk.CTkFont(size=10),
            text_color=("gray35", "gray65"),
        ).pack(anchor="w", padx=6)

        # ----------------- FORM ACTION BUTTONS (STRICTLY AT BOTTOM) -----------------
        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(6, 10))

        self.btn_submit = ctk.CTkButton(
            btn_frame,
            text=t("btn_add_drop"),
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=38,
            command=self._handle_submit,
        )
        self.btn_submit.pack(side="left", padx=(0, 10))

        self.btn_cancel_edit = ctk.CTkButton(
            btn_frame,
            text=t("btn_reset_form"),
            fg_color="transparent",
            border_width=1,
            height=38,
            width=110,
            command=self._reset_form,
        )
        self.btn_cancel_edit.pack(side="left")

        # Attach i18n Hover Tooltips to all interactables
        create_tooltip(self.combo_engine, t("tooltip_engine"))
        create_tooltip(self.combo_intent, t("tooltip_intent"))
        create_tooltip(self.entry_scope, t("tooltip_scope"))
        create_tooltip(self.txt_prompt, t("tooltip_prompt"))
        create_tooltip(self.txt_output, t("tooltip_output"))
        create_tooltip(self.switch_critical, t("tooltip_crit_toggle"))
        create_tooltip(self.switch_factcheck, t("tooltip_fc_toggle"))
        create_tooltip(self.btn_submit, t("tooltip_add_drop"))
        create_tooltip(self.btn_cancel_edit, t("tooltip_reset_drop"))

        # ----------------- RIGHT: Active Session Drops List -----------------
        right_container = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        right_container.grid(row=0, column=1, sticky="nsew", padx=(6, 10), pady=10)

        header_right = ctk.CTkFrame(right_container, fg_color="transparent")
        header_right.pack(fill="x", padx=12, pady=(10, 6))

        self.lbl_drops_count = ctk.CTkLabel(
            header_right,
            text=t("log_session_drops_title", count=len(self.doc.drops)),
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.lbl_drops_count.pack(side="left")

        self.scroll_drops = ctk.CTkScrollableFrame(right_container, fg_color="transparent")
        self.scroll_drops.pack(fill="both", expand=True, padx=8, pady=(0, 10))

    def _build_critical_frame(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        # Wizard instruction / subtitle
        ctk.CTkLabel(
            inner,
            text=t("crit_subhint_desc"),
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w", pady=(0, 6))

        # Field 1: Plausibility Flaws
        ctk.CTkLabel(
            inner,
            text=t("lbl_crit_flaws"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=t("crit_flaws_hint"),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w")

        self.txt_flaws = ctk.CTkTextbox(inner, height=60, font=ctk.CTkFont(size=12))
        self.txt_flaws.pack(fill="x", pady=(2, 8))

        # Field 2: Application Decision
        ctk.CTkLabel(
            inner,
            text=t("lbl_decision"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            inner,
            text=t("crit_decision_hint"),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w")

        localized_decisions = get_localized_decisions()
        self.var_decision = ctk.StringVar(value=localized_decisions[0])
        self.seg_decision = ctk.CTkSegmentedButton(
            inner,
            values=localized_decisions,
            variable=self.var_decision,
            selected_color="#2b6cb0",
            selected_hover_color="#1a365d",
        )
        self.seg_decision.pack(anchor="w", pady=(3, 4))

    def _build_factcheck_frame(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        # Wizard instruction / subtitle
        ctk.CTkLabel(
            inner,
            text=t("fc_subhint_desc"),
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w", pady=(0, 6))

        # Claim to Verify
        ctk.CTkLabel(inner, text=t("lbl_fc_claim"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(inner, text=t("fc_claim_hint"), font=ctk.CTkFont(size=10), text_color=("gray40", "gray60")).pack(anchor="w")
        self.var_fc_claim = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.var_fc_claim, placeholder_text=t("ph_fc_claim"), height=30).pack(fill="x", pady=(2, 6))

        # Primary Source Citation
        ctk.CTkLabel(inner, text=t("lbl_fc_source"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(inner, text=t("fc_source_hint"), font=ctk.CTkFont(size=10), text_color=("gray40", "gray60")).pack(anchor="w")
        self.var_fc_source = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.var_fc_source, placeholder_text=t("ph_fc_source"), height=30).pack(fill="x", pady=(2, 6))

        # Verification Status
        ctk.CTkLabel(inner, text=t("lbl_fc_status"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(inner, text=t("fc_status_hint"), font=ctk.CTkFont(size=10), text_color=("gray40", "gray60")).pack(anchor="w")
        localized_statuses = get_localized_statuses()
        self.var_fc_status = ctk.StringVar(value=localized_statuses[0])
        combo_status = ctk.CTkComboBox(inner, values=localized_statuses, variable=self.var_fc_status, height=30, width=220)
        combo_status.pack(anchor="w", pady=(2, 6))

        # Rectification Note
        ctk.CTkLabel(inner, text=t("lbl_fc_note"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(inner, text=t("fc_note_hint"), font=ctk.CTkFont(size=10), text_color=("gray40", "gray60")).pack(anchor="w")
        self.var_fc_note = ctk.StringVar()
        ctk.CTkEntry(inner, textvariable=self.var_fc_note, placeholder_text=t("ph_fc_note"), height=30).pack(fill="x", pady=(2, 4))

    def _toggle_critical_frame(self):
        if self.var_enable_critical.get():
            self.frame_critical.pack(fill="x", pady=(0, 6))
        else:
            self.frame_critical.pack_forget()

    def _toggle_factcheck_frame(self):
        if self.var_enable_factcheck.get():
            self.frame_factcheck.pack(fill="x", pady=(0, 6))
        else:
            self.frame_factcheck.pack_forget()

    def _refresh_timestamp(self):
        self.var_timestamp.set(get_current_cest_time())

    def _reset_form(self):
        self.editing_drop_id = None
        self.lbl_form_header.configure(text=t("log_heading_new"))
        self.btn_submit.configure(text=t("btn_add_drop"))
        self._refresh_timestamp()
        # Keep the engine you were using!
        self.var_engine.set(self.storage.last_used_engine)
        self.var_intent.set(get_localized_intents()[0])
        self.var_scope.set("")
        self.var_file_ref.set("")
        self.txt_prompt.delete("1.0", "end")
        self.txt_output.delete("1.0", "end")
        self.txt_flaws.delete("1.0", "end")
        self.var_decision.set(get_localized_decisions()[0])
        self.var_fc_claim.set("")
        self.var_fc_source.set("")
        self.var_fc_status.set(get_localized_statuses()[0])
        self.var_fc_note.set("")
        self.var_enable_critical.set(False)
        self.var_enable_factcheck.set(False)
        self._toggle_critical_frame()
        self._toggle_factcheck_frame()

    def _handle_submit(self):
        prompt = self.txt_prompt.get("1.0", "end-1c").strip()
        raw_output_text = self.txt_output.get("1.0", "end-1c").strip()
        # Always auto-clean output on save to guarantee bulletproof PDF rendering
        output = clean_raw_interaction_text(raw_output_text)
        file_ref = self.var_file_ref.get().strip()

        # Gentle validation: only warn if prompt, output, and file_ref are all empty
        if not prompt and not output and not file_ref:
            messagebox.showwarning("Validation", t("val_prompt_required"))
            return

        engine = self.var_engine.get().strip() or "Anthropic Claude"
        self.storage.last_used_engine = engine

        crit_exam: Optional[CriticalExamination] = None
        fact_checks: List[FactCheckEntry] = []

        if self.var_enable_critical.get():
            flaws = self.txt_flaws.get("1.0", "end-1c").strip()
            raw_decision = self.var_decision.get()
            canonical_decision = canonicalize_decision(raw_decision)
            crit_exam = CriticalExamination(flaws_plausibility=flaws, application_decision=canonical_decision)

        if self.var_enable_factcheck.get():
            claim = self.var_fc_claim.get().strip()
            if claim:
                raw_status = self.var_fc_status.get()
                canonical_stat = canonicalize_status(raw_status)
                fc = FactCheckEntry(
                    claim=claim,
                    primary_source=self.var_fc_source.get().strip(),
                    status=canonical_stat,
                    rectification_note=self.var_fc_note.get().strip(),
                )
                fact_checks.append(fc)

        raw_intent = self.var_intent.get().strip()
        canonical_intent = canonicalize_intent(raw_intent)

        if self.editing_drop_id:
            target_drop = next((d for d in self.doc.drops if d.id == self.editing_drop_id), None)
            if target_drop:
                target_drop.timestamp = self.var_timestamp.get().strip() or get_current_cest_time()
                target_drop.target_engine = self.var_engine.get().strip()
                target_drop.core_intent = canonical_intent
                target_drop.context_scope = self.var_scope.get().strip()
                target_drop.raw_prompt = prompt
                target_drop.raw_output = output
                target_drop.output_file_reference = file_ref
                target_drop.critical_examination = crit_exam
                target_drop.fact_checks = fact_checks
        else:
            new_drop = InteractionDrop(
                timestamp=self.var_timestamp.get().strip() or get_current_cest_time(),
                target_engine=self.var_engine.get().strip(),
                core_intent=canonical_intent,
                context_scope=self.var_scope.get().strip(),
                raw_prompt=prompt,
                raw_output=output,
                output_file_reference=file_ref,
                critical_examination=crit_exam,
                fact_checks=fact_checks,
            )
            self.doc.drops.append(new_drop)

        self.doc.renumber_drops()
        self._reset_form()
        self.refresh_drops_list()
        self.on_document_changed()

    def refresh_drops_list(self):
        for widget in self.scroll_drops.winfo_children():
            widget.destroy()

        self.lbl_drops_count.configure(text=t("log_session_drops_title", count=len(self.doc.drops)))

        if not self.doc.drops:
            lbl_empty = ctk.CTkLabel(
                self.scroll_drops,
                text=t("log_empty_drops"),
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray50"),
                justify="center",
            )
            lbl_empty.pack(pady=40)
            return

        for drop in self.doc.drops:
            self._render_drop_card(drop)

    def _render_drop_card(self, drop: InteractionDrop):
        card = ctk.CTkFrame(
            self.scroll_drops,
            corner_radius=8,
            fg_color=("white", "gray19"),
            border_width=1,
            border_color=("gray85", "gray26"),
        )
        card.pack(fill="x", pady=4, padx=2)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(8, 2))

        loc_intent = localize_intent(drop.core_intent)
        lbl_num = ctk.CTkLabel(
            hdr,
            text=f"#{drop.drop_number} {loc_intent}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        lbl_num.pack(side="left")

        lbl_engine = ctk.CTkLabel(
            hdr,
            text=f"{drop.target_engine}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        )
        lbl_engine.pack(side="right")

        b_row = ctk.CTkFrame(card, fg_color="transparent")
        b_row.pack(fill="x", padx=10, pady=(0, 4))

        decision = drop.critical_examination.application_decision if drop.critical_examination else "Accepted"
        loc_decision = localize_decision(decision)
        color_map = {
            "Accepted": ("#c6f6d5", "#22543d"),
            "Modified": ("#fefcbf", "#744210"),
            "Rejected": ("#fed7d7", "#742a2a"),
        }
        bg_col, txt_col = color_map.get(decision, ("#edf2f7", "#4a5568"))

        lbl_dec = ctk.CTkLabel(
            b_row,
            text=loc_decision,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=bg_col,
            text_color=txt_col,
            corner_radius=4,
            padx=6,
            pady=1,
        )
        lbl_dec.pack(side="left", padx=(0, 6))

        if drop.fact_checks:
            lbl_fc = ctk.CTkLabel(
                b_row,
                text=t("badge_fact_checks", count=len(drop.fact_checks)),
                font=ctk.CTkFont(size=10),
                text_color=("#2b6cb0", "#90cdf4"),
            )
            lbl_fc.pack(side="left")

        snippet = drop.raw_prompt.replace("\n", " ").strip()
        if len(snippet) > 75:
            snippet = snippet[:72] + "..."
        lbl_snip = ctk.CTkLabel(
            card,
            text=f'"{snippet}"',
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
            anchor="w",
            justify="left",
        )
        lbl_snip.pack(fill="x", padx=10, pady=(2, 6))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=10, pady=(0, 8))

        btn_edit = ctk.CTkButton(
            actions,
            text=t("btn_edit"),
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("#2b6cb0", "#3182ce"),
            command=lambda d=drop: self._load_drop_into_form(d),
        )
        btn_edit.pack(side="right", padx=(4, 0))

        btn_del = ctk.CTkButton(
            actions,
            text=t("btn_delete"),
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#e53e3e", "#fc8181"),
            border_width=1,
            hover_color=("gray90", "gray28"),
            command=lambda d=drop: self._delete_drop(d),
        )
        btn_del.pack(side="right")

    def _load_drop_into_form(self, drop: InteractionDrop):
        self.editing_drop_id = drop.id
        self.lbl_form_header.configure(text=t("log_heading_edit", num=drop.drop_number))
        self.btn_submit.configure(text=t("btn_update_drop", num=drop.drop_number))

        self.var_timestamp.set(drop.timestamp)
        self.var_engine.set(drop.target_engine)
        self.var_intent.set(localize_intent(drop.core_intent))
        self.var_scope.set(drop.context_scope)
        self.var_file_ref.set(drop.output_file_reference or "")

        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("1.0", drop.raw_prompt)

        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", drop.raw_output)

        if drop.critical_examination:
            self.var_enable_critical.set(True)
            self._toggle_critical_frame()
            self.txt_flaws.delete("1.0", "end")
            self.txt_flaws.insert("1.0", drop.critical_examination.flaws_plausibility)
            self.var_decision.set(localize_decision(drop.critical_examination.application_decision))
        else:
            self.var_enable_critical.set(False)
            self._toggle_critical_frame()

        if drop.fact_checks:
            self.var_enable_factcheck.set(True)
            self._toggle_factcheck_frame()
            fc = drop.fact_checks[0]
            self.var_fc_claim.set(fc.claim)
            self.var_fc_source.set(fc.primary_source)
            self.var_fc_status.set(localize_status(fc.status))
            self.var_fc_note.set(fc.rectification_note)
        else:
            self.var_enable_factcheck.set(False)
            self._toggle_factcheck_frame()

    def _delete_drop(self, drop: InteractionDrop):
        confirm = messagebox.askyesno(
            t("confirm_delete_title"),
            t("confirm_delete_drop_msg", num=drop.drop_number),
        )
        if confirm:
            if self.editing_drop_id == drop.id:
                self._reset_form()
            self.doc.drops.remove(drop)
            self.doc.renumber_drops()
            self.refresh_drops_list()
            self.on_document_changed()

    def _on_output_paste(self):
        """Automatically sanitizes output on paste and triggers non-blocking toast feedback."""
        raw = self.txt_output.get("1.0", "end-1c")
        if raw.strip():
            cleaned = clean_raw_interaction_text(raw)
            if cleaned != raw:
                self.txt_output.delete("1.0", "end")
                self.txt_output.insert("1.0", cleaned)
            self._show_toast(t("toast_sanitized"))

    def _show_toast(self, msg: str):
        """Shows non-intrusive feedback toast next to Output label, auto-hiding after 2.5s."""
        self.lbl_toast.configure(text=msg)
        self.after(2500, lambda: self.lbl_toast.configure(text=""))

    def _tidy_output_text(self):
        """Cleans and standardizes the AI output text in the textbox."""
        raw = self.txt_output.get("1.0", "end").rstrip("\n")
        if raw.strip():
            cleaned = clean_raw_interaction_text(raw)
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", cleaned)
            self._show_toast(t("toast_sanitized"))

