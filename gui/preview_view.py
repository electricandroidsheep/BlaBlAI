"""
Live Markdown Preview & Document Exporter View.
Provides real-time Markdown preview, clipboard copy, standalone Markdown export,
and publication-grade PDF rendering with automatic PDF viewer launch.
Localized for English and German.
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable

from models import ProtocolDocument
from generator import (
    generate_markdown,
    render_to_pdf,
    open_in_system_viewer,
)
from i18n import t


class PreviewView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        doc: ProtocolDocument,
        on_status_msg: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.doc = doc
        self.on_status_msg = on_status_msg

        self._build_ui()
        self.refresh_preview()

    def _build_ui(self):
        for w in self.winfo_children():
            w.destroy()

        # 1. Action Bar at Top
        action_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        action_bar.pack(fill="x", padx=16, pady=(12, 8))

        # Title
        ctk.CTkLabel(
            action_bar,
            text=t("prev_title"),
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        ).pack(side="left", padx=14, pady=10)

        # Buttons on the right
        btn_box = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_box.pack(side="right", padx=10, pady=8)

        self.btn_copy = ctk.CTkButton(
            btn_box,
            text=t("btn_copy_markdown"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray95"),
            hover_color=("gray70", "gray35"),
            height=34,
            command=self._handle_copy_clipboard,
        )
        self.btn_copy.pack(side="left", padx=4)

        btn_export_md = ctk.CTkButton(
            btn_box,
            text=t("btn_save_md"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray95"),
            hover_color=("gray70", "gray35"),
            height=34,
            command=self._handle_export_markdown,
        )
        btn_export_md.pack(side="left", padx=4)

        btn_render_pdf = ctk.CTkButton(
            btn_box,
            text=t("btn_render_pdf"),
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=34,
            command=self._handle_render_pdf,
        )
        btn_render_pdf.pack(side="left", padx=4)

        btn_refresh = ctk.CTkButton(
            btn_box,
            text="↺",
            width=34,
            height=34,
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            border_width=1,
            command=self.refresh_preview,
        )
        btn_refresh.pack(side="left", padx=4)

        # 2. Textbox Preview Area
        preview_container = ctk.CTkFrame(self, corner_radius=10, fg_color=("gray95", "gray14"))
        preview_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self.txt_preview = ctk.CTkTextbox(
            preview_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            corner_radius=8,
        )
        self.txt_preview.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_preview(self):
        """Re-compiles Markdown and updates text viewer."""
        md_text = generate_markdown(self.doc)
        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", md_text)
        self.txt_preview.configure(state="disabled")

    def _handle_copy_clipboard(self):
        md_text = generate_markdown(self.doc)
        self.clipboard_clear()
        self.clipboard_append(md_text)

        # Temporary button feedback
        self.btn_copy.configure(text=t("btn_copied"), fg_color="#38a169")
        self.after(1800, lambda: self.btn_copy.configure(text=t("btn_copy_markdown"), fg_color=("gray80", "gray25")))

        if self.on_status_msg:
            self.on_status_msg(t("status_copied"))

    def _handle_export_markdown(self):
        safe_title = "".join(c for c in self.doc.title if c.isalnum() or c in (" ", "_", "-")).strip()
        safe_title = safe_title.replace(" ", "_") or "AI_Protocol"
        default_filename = f"{safe_title}.md"

        file_path = filedialog.asksaveasfilename(
            title="Export Protocol to Markdown",
            defaultextension=".md",
            initialfile=default_filename,
            filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            md_text = generate_markdown(self.doc)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            messagebox.showinfo(t("export_success_title"), t("export_success_msg", path=file_path))
        except Exception as e:
            messagebox.showerror(t("export_failed_title"), f"Failed to save Markdown:\n{e}")

    def _handle_render_pdf(self):
        safe_title = "".join(c for c in self.doc.title if c.isalnum() or c in (" ", "_", "-")).strip()
        safe_title = safe_title.replace(" ", "_") or "AI_Protocol"
        default_filename = f"{safe_title}.pdf"

        file_path = filedialog.asksaveasfilename(
            title="Render Protocol to PDF",
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            render_to_pdf(self.doc, file_path)
            open_in_system_viewer(file_path)
            if self.on_status_msg:
                self.on_status_msg(t("status_pdf_rendered", name=Path(file_path).name))
        except Exception as e:
            messagebox.showerror(t("pdf_error_title"), f"Failed to render PDF:\n{e}")
