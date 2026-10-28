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

from datetime import datetime, timezone, timedelta
from models import (
    ProtocolDocument,
    InteractionDrop,
    CriticalExamination,
    FactCheckEntry,
    get_current_cest_time,
    get_current_date,
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
        self.form_scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        form_scroll = self.form_scroll
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

        f_time_lbl_row = ctk.CTkFrame(f_time, fg_color="transparent")
        f_time_lbl_row.pack(fill="x")
        ctk.CTkLabel(f_time_lbl_row, text=t("lbl_timestamp"), font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        self.var_retroactive = ctk.BooleanVar(value=False)
        self.cb_retroactive = ctk.CTkCheckBox(
            f_time_lbl_row,
            text=t("lbl_retroactive"),
            variable=self.var_retroactive,
            font=ctk.CTkFont(size=11),
            height=18,
            checkbox_width=16,
            checkbox_height=16,
            command=self._on_retroactive_toggled,
        )
        self.cb_retroactive.pack(side="right")
        create_tooltip(self.cb_retroactive, t("tooltip_retroactive"))

        f_time_input = ctk.CTkFrame(f_time, fg_color="transparent")
        f_time_input.pack(fill="x", pady=(2, 0))
        self.var_timestamp = ctk.StringVar(value=get_current_cest_time())
        self.entry_timestamp = ctk.CTkEntry(f_time_input, textvariable=self.var_timestamp, height=32)
        self.entry_timestamp.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_calendar = ctk.CTkButton(
            f_time_input,
            text=t("btn_pick_datetime"),
            width=36,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray35"),
            command=self._open_datetime_picker,
        )
        self.btn_calendar.pack(side="left", padx=(0, 4))
        create_tooltip(self.btn_calendar, t("tooltip_pick_datetime"))

        btn_refresh_time = ctk.CTkButton(
            f_time_input,
            text=t("btn_now"),
            width=50,
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

        # Interaction Title (Optional)
        f_title = ctk.CTkFrame(form_scroll, fg_color="transparent")
        f_title.pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(f_title, text=t("lbl_drop_title"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.var_drop_title = ctk.StringVar(value="")
        self.entry_drop_title = ctk.CTkEntry(
            f_title,
            textvariable=self.var_drop_title,
            placeholder_text=t("ph_drop_title"),
            height=32,
        )
        self.entry_drop_title.pack(fill="x", pady=(2, 0))

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

        # ----------------- CRITICAL REFLECTION & APPLICATION DECISION (OPTIONAL) -----------------
        self.frame_critical = ctk.CTkFrame(form_scroll, corner_radius=8, fg_color=("gray90", "gray18"))
        self.frame_critical.pack(fill="x", pady=(6, 4))
        self._build_critical_frame(self.frame_critical)

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
        create_tooltip(self.btn_submit, t("tooltip_add_drop"))
        create_tooltip(self.btn_cancel_edit, t("tooltip_reset_drop"))

        # Ensure nested textboxes inside form_scroll do not hijack or stall form scrolling
        for nested_tb in (self.txt_prompt, self.txt_output, self.txt_flaws):
            self._bind_nested_textbox_scroll(nested_tb)

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

    def _bind_nested_textbox_scroll(self, ctk_tb: ctk.CTkTextbox) -> None:
        """
        Prevents nested CTkTextbox widgets inside form_scroll from swallowing scroll events
        when they do not have keyboard focus or have reached their top/bottom scroll boundary.
        """
        tb = getattr(ctk_tb, "_textbox", None)
        if not tb:
            return

        def _can_tb_scroll(scroll_down: bool) -> bool:
            try:
                if self.focus_get() != tb:
                    return False
                y0, y1 = tb.yview()
                if y0 <= 0.0 and y1 >= 1.0:
                    return False
                return (y1 < 1.0) if scroll_down else (y0 > 0.0)
            except Exception:
                return False

        def _on_tb_touchpad(event):
            raw = int(getattr(event, "delta", 0))
            low = raw & 0xFFFF
            dy = low if low < 0x8000 else low - 0x10000
            if _can_tb_scroll(scroll_down=(dy < 0)):
                return
            top = self.winfo_toplevel()
            if hasattr(top, "_scroll_container_by_touchpad"):
                top._scroll_container_by_touchpad(self.form_scroll, event)
                return "break"

        def _on_tb_wheel(event):
            delta = getattr(event, "delta", 0)
            if _can_tb_scroll(scroll_down=(delta < 0)):
                return
            top = self.winfo_toplevel()
            if hasattr(top, "_scroll_container_by_wheel"):
                top._scroll_container_by_wheel(self.form_scroll, event)
                return "break"

        try:
            tb.bind("<TouchpadScroll>", _on_tb_touchpad)
        except Exception:
            pass
        for seq in ("<MouseWheel>", "<Shift-MouseWheel>"):
            try:
                tb.bind(seq, _on_tb_wheel)
            except Exception:
                pass

    def _build_critical_frame(self, parent):
        # Section Header
        ctk.CTkLabel(
            parent,
            text=f"🧐 {t('lbl_critical_section_optional')}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        ).pack(anchor="w", padx=14, pady=(10, 2))

        # Wizard instruction / subtitle
        ctk.CTkLabel(
            parent,
            text=t("crit_subhint_desc"),
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # Field 1: Plausibility Flaws
        ctk.CTkLabel(
            parent,
            text=t("lbl_crit_flaws"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=14)

        ctk.CTkLabel(
            parent,
            text=t("crit_flaws_hint"),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w", padx=14)

        self.txt_flaws = ctk.CTkTextbox(parent, height=60, font=ctk.CTkFont(size=12))
        self.txt_flaws.pack(fill="x", padx=14, pady=(2, 8))

        # Field 2: Application Decision
        ctk.CTkLabel(
            parent,
            text=t("lbl_decision"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=14)

        ctk.CTkLabel(
            parent,
            text=t("crit_decision_hint"),
            font=ctk.CTkFont(size=10),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w", padx=14)

        localized_decisions = get_localized_decisions()
        self.var_decision = ctk.StringVar(value=localized_decisions[0])
        self.seg_decision = ctk.CTkSegmentedButton(
            parent,
            values=localized_decisions,
            variable=self.var_decision,
            selected_color="#2b6cb0",
            selected_hover_color="#1a365d",
        )
        self.seg_decision.pack(anchor="w", padx=14, pady=(3, 12))

    def _open_datetime_picker(self):
        from gui.datetime_picker import DateTimePickerDialog

        def _on_apply(new_ts: str, is_retro: bool):
            self.var_timestamp.set(new_ts)
            self.var_retroactive.set(is_retro)

        DateTimePickerDialog(
            self.winfo_toplevel(),
            initial_timestamp=self.var_timestamp.get(),
            is_retroactive=self.var_retroactive.get(),
            on_apply=_on_apply,
        )

    def _on_retroactive_toggled(self):
        curr = self.var_timestamp.get().strip()
        date_part = curr.split()[0] if curr else get_current_date()
        if self.var_retroactive.get():
            self.var_timestamp.set(f"{date_part} (Retroactive)")
        else:
            time_now = datetime.now(timezone(timedelta(hours=2))).strftime("%H:%M")
            self.var_timestamp.set(f"{date_part} {time_now} CEST")

    def _refresh_timestamp(self):
        if self.var_retroactive.get():
            self.var_timestamp.set(f"{get_current_date()} (Retroactive)")
        else:
            self.var_timestamp.set(get_current_cest_time())

    def _reset_form(self):
        self.editing_drop_id = None
        self.lbl_form_header.configure(text=t("log_heading_new"))
        self.btn_submit.configure(text=t("btn_add_drop"))
        self.var_retroactive.set(False)
        self._refresh_timestamp()
        # Keep the engine you were using!
        self.var_engine.set(self.storage.last_used_engine)
        self.var_drop_title.set("")
        self.var_intent.set(get_localized_intents()[0])
        self.var_scope.set("")
        self.var_file_ref.set("")
        self.txt_prompt.delete("1.0", "end")
        self.txt_output.delete("1.0", "end")
        self.txt_flaws.delete("1.0", "end")
        self.var_decision.set(get_localized_decisions()[0])

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

        flaws = self.txt_flaws.get("1.0", "end-1c").strip()
        raw_decision = self.var_decision.get()
        canonical_decision = canonicalize_decision(raw_decision)
        crit_exam = CriticalExamination(flaws_plausibility=flaws, application_decision=canonical_decision)

        drop_title = self.var_drop_title.get().strip()
        raw_intent = self.var_intent.get().strip()
        canonical_intent = canonicalize_intent(raw_intent)
        is_retro = self.var_retroactive.get()

        if self.editing_drop_id:
            target_drop = next((d for d in self.doc.drops if d.id == self.editing_drop_id), None)
            if target_drop:
                target_drop.timestamp = self.var_timestamp.get().strip() or get_current_cest_time()
                target_drop.title = drop_title
                target_drop.target_engine = self.var_engine.get().strip()
                target_drop.core_intent = canonical_intent
                target_drop.context_scope = self.var_scope.get().strip()
                target_drop.raw_prompt = prompt
                target_drop.raw_output = output
                target_drop.output_file_reference = file_ref
                target_drop.is_retroactive = is_retro
                target_drop.critical_examination = crit_exam
        else:
            new_drop = InteractionDrop(
                timestamp=self.var_timestamp.get().strip() or get_current_cest_time(),
                title=drop_title,
                target_engine=self.var_engine.get().strip(),
                core_intent=canonical_intent,
                context_scope=self.var_scope.get().strip(),
                raw_prompt=prompt,
                raw_output=output,
                output_file_reference=file_ref,
                is_retroactive=is_retro,
                critical_examination=crit_exam,
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
        is_editing_this = (self.editing_drop_id == drop.id)
        border_col = ("#3182ce", "#63b3ed") if is_editing_this else ("gray85", "gray26")
        card = ctk.CTkFrame(
            self.scroll_drops,
            corner_radius=8,
            fg_color=("white", "gray19"),
            border_width=2 if is_editing_this else 1,
            border_color=border_col,
            cursor="hand2",
        )
        card.pack(fill="x", pady=4, padx=2)
        on_edit_click = lambda e, d=drop: self._load_drop_into_form(d)
        card.bind("<Double-Button-1>", on_edit_click)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(8, 2))

        loc_intent = localize_intent(drop.core_intent)
        card_title = f"#{drop.drop_number} {drop.title.strip()}" if drop.title and drop.title.strip() else f"#{drop.drop_number} {loc_intent}"
        lbl_num = ctk.CTkLabel(
            hdr,
            text=card_title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
            cursor="hand2",
        )
        lbl_num.pack(side="left")
        lbl_num.bind("<Double-Button-1>", on_edit_click)

        if drop.is_retroactive:
            lbl_retro = ctk.CTkLabel(
                hdr,
                text=f"[{t('badge_retroactive')}]",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("#4a5568", "#a0aec0"),
                fg_color=("gray85", "gray25"),
                corner_radius=4,
                padx=5,
                pady=1,
            )
            lbl_retro.pack(side="left", padx=(6, 0))

        lbl_engine = ctk.CTkLabel(
            hdr,
            text=f"{drop.target_engine}",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
            cursor="hand2",
        )
        lbl_engine.pack(side="right")
        lbl_engine.bind("<Double-Button-1>", on_edit_click)

        b_row = ctk.CTkFrame(card, fg_color="transparent")
        b_row.pack(fill="x", padx=10, pady=(0, 4))

        if drop.title and drop.title.strip():
            lbl_intent_tag = ctk.CTkLabel(
                b_row,
                text=loc_intent,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=("gray85", "gray25"),
                text_color=("gray20", "gray85"),
                corner_radius=4,
                padx=5,
                pady=1,
                cursor="hand2",
            )
            lbl_intent_tag.pack(side="left", padx=(0, 6))
            lbl_intent_tag.bind("<Double-Button-1>", on_edit_click)

        decision = drop.critical_examination.application_decision if drop.critical_examination else "N/A"
        loc_decision = localize_decision(decision)
        color_map = {
            "N/A": (("gray85", "gray25"), ("gray35", "gray75")),
            "Accepted": ("#c6f6d5", "#22543d"),
            "Modified": ("#fefcbf", "#744210"),
            "Rejected": ("#fed7d7", "#742a2a"),
        }
        bg_col, txt_col = color_map.get(decision, (("gray85", "gray25"), ("gray35", "gray75")))

        lbl_dec = ctk.CTkLabel(
            b_row,
            text=loc_decision,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=bg_col,
            text_color=txt_col,
            corner_radius=4,
            padx=6,
            pady=1,
            cursor="hand2",
        )
        lbl_dec.pack(side="left", padx=(0, 6))
        lbl_dec.bind("<Double-Button-1>", on_edit_click)

        if drop.fact_checks:
            lbl_fc = ctk.CTkLabel(
                b_row,
                text=t("badge_fact_checks", count=len(drop.fact_checks)),
                font=ctk.CTkFont(size=10),
                text_color=("#2b6cb0", "#90cdf4"),
                cursor="hand2",
            )
            lbl_fc.pack(side="left")
            lbl_fc.bind("<Double-Button-1>", on_edit_click)

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
            cursor="hand2",
        )
        lbl_snip.pack(fill="x", padx=10, pady=(2, 6))
        lbl_snip.bind("<Double-Button-1>", on_edit_click)

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

        self.var_retroactive.set(drop.is_retroactive)
        self.var_timestamp.set(drop.timestamp)
        self.var_drop_title.set(drop.title or "")
        self.var_engine.set(drop.target_engine)
        self.var_intent.set(localize_intent(drop.core_intent))
        self.var_scope.set(drop.context_scope)
        self.var_file_ref.set(drop.output_file_reference or "")

        self.txt_prompt.delete("1.0", "end")
        self.txt_prompt.insert("1.0", drop.raw_prompt)

        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", drop.raw_output)

        self.txt_flaws.delete("1.0", "end")
        if drop.critical_examination:
            if drop.critical_examination.flaws_plausibility:
                self.txt_flaws.insert("1.0", drop.critical_examination.flaws_plausibility)
            self.var_decision.set(localize_decision(drop.critical_examination.application_decision))
        else:
            self.var_decision.set(get_localized_decisions()[0])

    def _delete_drop(self, drop: InteractionDrop):
        confirm = messagebox.askyesno(
            t("confirm_delete_title"),
            t("confirm_delete_drop_msg", num=drop.drop_number),
        )
        if confirm:
            if self.editing_drop_id == drop.id:
                self._reset_form()
            self.doc.remove_drop(drop)
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

