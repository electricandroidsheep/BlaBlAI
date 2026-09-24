"""
Global Student Profile & Institutional Defaults Settings Dialog.
Allows configuring student identity (Name, Degree, Matrikelnummer)
and customized dual-language Academic AI Affidavit statements.
"""

from __future__ import annotations
import customtkinter as ctk
from typing import Optional, Callable
from storage import StorageManager, DEFAULT_AFFIDAVIT_EN, DEFAULT_AFFIDAVIT_DE
from i18n import t
from gui.tooltip import create_tooltip


class ProfileSettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        storage: StorageManager,
        on_save: Optional[Callable[[], None]] = None,
        is_onboarding: bool = False,
    ):
        super().__init__(parent)
        self.storage = storage
        self.on_save = on_save
        self.is_onboarding = is_onboarding

        self.title(t("onboarding_welcome_title") if is_onboarding else t("profile_heading"))
        self.geometry("620x720")
        self.minsize(520, 560)
        self.grab_set()

        self._build_ui()
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
        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=20, pady=(16, 12))

        # Onboarding banner if first launch
        if self.is_onboarding:
            onboard_card = ctk.CTkFrame(main_box, fg_color=("#ebf8ff", "#2a4365"), corner_radius=6)
            onboard_card.pack(fill="x", pady=(0, 10), padx=2, ipadx=10, ipady=8)
            ctk.CTkLabel(
                onboard_card,
                text=t("onboarding_welcome_title"),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#2b6cb0", "#90cdf4"),
            ).pack(anchor="w")
            ctk.CTkLabel(
                onboard_card,
                text=t("onboarding_welcome_desc"),
                font=ctk.CTkFont(size=11),
                text_color=("#2d3748", "#e2e8f0"),
                wraplength=540,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

        # Title
        ctk.CTkLabel(
            main_box,
            text=t("profile_heading"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            main_box,
            text=t("profile_subheading"),
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w", pady=(0, 10))

        # Scrollable form container
        scroll = ctk.CTkScrollableFrame(main_box, fg_color=("gray95", "gray15"), corner_radius=8)
        scroll.pack(fill="both", expand=True, pady=(0, 10))

        # Section 1: Academic Credentials
        ctk.CTkLabel(
            scroll,
            text="Personal Academic Identity",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        ).pack(anchor="w", padx=6, pady=(6, 4))

        # Student Name
        ctk.CTkLabel(scroll, text=t("lbl_student_name"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.var_name = ctk.StringVar(value=self.storage.student_name)
        entry_name = ctk.CTkEntry(scroll, textvariable=self.var_name, height=32)
        entry_name.pack(fill="x", padx=6, pady=(0, 6))
        create_tooltip(entry_name, t("tooltip_profile_name"))

        # Degree Program
        ctk.CTkLabel(scroll, text=t("lbl_degree_program"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.var_degree = ctk.StringVar(value=self.storage.degree_program)
        entry_degree = ctk.CTkEntry(scroll, textvariable=self.var_degree, height=32)
        entry_degree.pack(fill="x", padx=6, pady=(0, 6))
        create_tooltip(entry_degree, t("tooltip_profile_degree"))

        # Matriculation Number
        ctk.CTkLabel(scroll, text=t("lbl_matriculation"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.var_matrikel = ctk.StringVar(value=self.storage.matriculation_number)
        entry_matrikel = ctk.CTkEntry(scroll, textvariable=self.var_matrikel, placeholder_text="e.g. k12345678 or 2210283001", height=32)
        entry_matrikel.pack(fill="x", padx=6, pady=(0, 12))
        create_tooltip(entry_matrikel, t("tooltip_profile_matriculation"))

        # Section 2: Custom Affidavit Declarations
        ctk.CTkLabel(
            scroll,
            text="Institutional AI Affidavit Statements",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        ).pack(anchor="w", padx=6, pady=(6, 2))

        ctk.CTkLabel(
            scroll,
            text="Customize the honor declaration texts included in exported PDFs and Markdown.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w", padx=6, pady=(0, 6))

        # English Affidavit
        ctk.CTkLabel(scroll, text=t("lbl_affidavit_en"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.txt_affidavit_en = ctk.CTkTextbox(scroll, height=90, font=ctk.CTkFont(size=11), wrap="word")
        self.txt_affidavit_en.pack(fill="x", padx=6, pady=(0, 8))
        self.txt_affidavit_en.insert("1.0", self.storage.custom_affidavit_en)

        # German Affidavit
        ctk.CTkLabel(scroll, text=t("lbl_affidavit_de"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=6, pady=(4, 2))
        self.txt_affidavit_de = ctk.CTkTextbox(scroll, height=90, font=ctk.CTkFont(size=11), wrap="word")
        self.txt_affidavit_de.pack(fill="x", padx=6, pady=(0, 8))
        self.txt_affidavit_de.insert("1.0", self.storage.custom_affidavit_de)

        # Reset Statements Button
        btn_reset_aff = ctk.CTkButton(
            scroll,
            text=f"↺ {t('btn_reset_affidavits')}",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            height=28,
            command=self._reset_affidavits,
        )
        btn_reset_aff.pack(anchor="w", padx=6, pady=(2, 8))

        # Bottom Bar
        btn_bar = ctk.CTkFrame(main_box, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(4, 0))

        btn_cancel = ctk.CTkButton(
            btn_bar,
            text=t("btn_cancel"),
            fg_color="transparent",
            border_width=1,
            width=100,
            command=self.destroy,
        )
        btn_cancel.pack(side="right", padx=(10, 0))

        btn_save = ctk.CTkButton(
            btn_bar,
            text=t("btn_save"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            width=130,
            command=self._handle_save,
        )
        btn_save.pack(side="right")

        # Tooltips
        create_tooltip(btn_reset_aff, "Revert statements to standard Austrian/EU academic honor declarations.")
        create_tooltip(btn_save, "Save profile defaults permanently to local configuration.")

    def _reset_affidavits(self):
        self.txt_affidavit_en.delete("1.0", "end")
        self.txt_affidavit_en.insert("1.0", DEFAULT_AFFIDAVIT_EN)
        self.txt_affidavit_de.delete("1.0", "end")
        self.txt_affidavit_de.insert("1.0", DEFAULT_AFFIDAVIT_DE)

    def _handle_save(self):
        self.storage.student_name = self.var_name.get().strip() or "Sven Várszegi, B.A."
        self.storage.degree_program = self.var_degree.get().strip() or "Master Digital Business Management (FH OÖ / JKU)"
        self.storage.matriculation_number = self.var_matrikel.get().strip()

        aff_en = self.txt_affidavit_en.get("1.0", "end").strip()
        aff_de = self.txt_affidavit_de.get("1.0", "end").strip()
        self.storage.custom_affidavit_en = aff_en or DEFAULT_AFFIDAVIT_EN
        self.storage.custom_affidavit_de = aff_de or DEFAULT_AFFIDAVIT_DE
        self.storage.onboarding_completed = True

        if self.on_save:
            self.on_save()

        self.destroy()
