"""
About & Help Dialog for BlaBlAI.
Displays scholarly rationale, academic authorship, and quick-start workflow instructions.
"""

from __future__ import annotations
import customtkinter as ctk
from i18n import t


class AboutHelpDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(t("about_dialog_title"))
        self.geometry("580x620")
        self.minsize(500, 520)
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
        main_box.pack(fill="both", expand=True, padx=20, pady=(16, 16))

        # Header Title
        header_frame = ctk.CTkFrame(main_box, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text="BlaBlAI",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_frame,
            text=t("about_dialog_title"),
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("gray40", "gray60"),
        ).pack(anchor="w")

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(main_box, fg_color=("gray95", "gray15"), corner_radius=8)
        scroll.pack(fill="both", expand=True, pady=(0, 12))

        # Author Card
        author_frame = ctk.CTkFrame(scroll, fg_color=("gray90", "gray20"), corner_radius=6)
        author_frame.pack(fill="x", padx=10, pady=(10, 8), ipadx=10, ipady=8)

        ctk.CTkLabel(
            author_frame,
            text=t("about_creator_label"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            author_frame,
            text=t("about_creator_name"),
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            author_frame,
            text=t("about_creator_affiliation"),
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(2, 0))

        # Academic Rationale & Integrity
        purpose_frame = ctk.CTkFrame(scroll, fg_color=("gray90", "gray20"), corner_radius=6)
        purpose_frame.pack(fill="x", padx=10, pady=8, ipadx=10, ipady=8)

        ctk.CTkLabel(
            purpose_frame,
            text=f"🎓 {t('about_purpose_title')}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            purpose_frame,
            text=t("about_purpose_desc"),
            font=ctk.CTkFont(size=11),
            text_color=("gray20", "gray80"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w")

        # 3-Step Workflow
        wf_frame = ctk.CTkFrame(scroll, fg_color=("gray90", "gray20"), corner_radius=6)
        wf_frame.pack(fill="x", padx=10, pady=8, ipadx=10, ipady=8)

        ctk.CTkLabel(
            wf_frame,
            text=f"📋 {t('about_workflow_title')}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 8))

        steps = [
            (t("about_step1_title"), t("about_step1_desc")),
            (t("about_step2_title"), t("about_step2_desc")),
            (t("about_step3_title"), t("about_step3_desc")),
        ]

        for step_title, step_desc in steps:
            step_box = ctk.CTkFrame(wf_frame, fg_color=("gray85", "gray25"), corner_radius=4)
            step_box.pack(fill="x", pady=4, padx=4, ipadx=6, ipady=6)

            ctk.CTkLabel(
                step_box,
                text=step_title,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w")

            ctk.CTkLabel(
                step_box,
                text=step_desc,
                font=ctk.CTkFont(size=10),
                text_color=("gray30", "gray70"),
                wraplength=460,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

        # Footer badge
        ctk.CTkLabel(
            scroll,
            text=t("about_license"),
            font=ctk.CTkFont(size=9),
            text_color=("gray50", "gray50"),
            wraplength=480,
            justify="center",
        ).pack(anchor="center", pady=(10, 6))

        # Bottom Close Button
        btn_frame = ctk.CTkFrame(main_box, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            btn_frame,
            text="OK",
            width=120,
            command=self.destroy,
        ).pack(anchor="center")
