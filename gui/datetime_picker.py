"""
Visual Date & Time Picker Dialog for BlaBlAI.
Provides a clean, interactive calendar grid and 24-hour time selector with support for
retroactive / archive (date-only) mode.
"""

from __future__ import annotations
import calendar
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
import customtkinter as ctk

from i18n import t, get_current_locale


class DateTimePickerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        initial_timestamp: str = "",
        is_retroactive: bool = False,
        on_apply: Optional[Callable[[str, bool], None]] = None,
    ):
        super().__init__(parent)
        self.on_apply = on_apply
        self.is_retroactive = is_retroactive

        # Determine initial date & time
        self.selected_year, self.selected_month, self.selected_day, self.selected_hour, self.selected_minute = self._parse_initial(initial_timestamp)

        self.title(t("dt_dialog_title"))
        self.geometry("380x480")
        self.resizable(False, False)

        # Modal configuration
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window(parent)

    def _parse_initial(self, ts_str: str):
        """Parses an existing timestamp string or returns current CEST values."""
        now = datetime.now(timezone(timedelta(hours=2)))
        year, month, day = now.year, now.month, now.day
        hour, minute = now.hour, now.minute

        clean = (ts_str or "").strip()
        if clean:
            # Handle standard "YYYY-MM-DD HH:MM CEST" or "YYYY-MM-DD (Retroactive)" or "YYYY-MM-DD"
            parts = clean.split()
            date_part = parts[0]
            try:
                dt_obj = datetime.strptime(date_part, "%Y-%m-%d")
                year, month, day = dt_obj.year, dt_obj.month, dt_obj.day
            except Exception:
                pass

            if len(parts) >= 2 and ":" in parts[1]:
                try:
                    time_parts = parts[1].split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                except Exception:
                    pass

        return year, month, day, hour, minute

    def _center_window(self, parent):
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w = 380
            h = 480
            x = max(0, px + (pw - w) // 2)
            y = max(0, py + (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=14)

        # 1. Month / Year Navigation Bar
        nav_frame = ctk.CTkFrame(container, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 6))

        btn_prev = ctk.CTkButton(
            nav_frame,
            text="◀",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._prev_month,
        )
        btn_prev.pack(side="left")

        month_names_en = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_names_de = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
        m_list = month_names_de if get_current_locale() == "de" else month_names_en
        m_name = m_list[self.selected_month]

        self.lbl_month_year = ctk.CTkLabel(
            nav_frame,
            text=f"{m_name} {self.selected_year}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1a365d", "#63b3ed"),
        )
        self.lbl_month_year.pack(side="left", fill="x", expand=True)

        btn_next = ctk.CTkButton(
            nav_frame,
            text="▶",
            width=32,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("gray80", "gray25"),
            text_color=("gray10", "gray90"),
            command=self._next_month,
        )
        btn_next.pack(side="right")

        # 2. Calendar Grid Container
        self.cal_frame = ctk.CTkFrame(container, fg_color=("gray92", "gray17"), corner_radius=8)
        self.cal_frame.pack(fill="x", pady=4, ipady=4)
        self._draw_calendar_days()

        # 3. Retroactive Checkbox
        self.var_retro = ctk.BooleanVar(value=self.is_retroactive)
        cb_retro = ctk.CTkCheckBox(
            container,
            text=t("lbl_retroactive"),
            variable=self.var_retro,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_retro_toggled,
        )
        cb_retro.pack(anchor="w", pady=(8, 4))

        # 4. Time Selection Row (Hour : Minute)
        self.time_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.time_frame.pack(fill="x", pady=(4, 6))

        ctk.CTkLabel(
            self.time_frame,
            text=t("dt_lbl_time"),
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 10))

        hours = [f"{i:02d}" for i in range(24)]
        minutes = [f"{i:02d}" for i in range(60)]

        self.var_hour = ctk.StringVar(value=f"{self.selected_hour:02d}")
        self.combo_hour = ctk.CTkComboBox(
            self.time_frame,
            values=hours,
            variable=self.var_hour,
            width=64,
            height=28,
            command=lambda _: self._update_preview(),
        )
        self.combo_hour.pack(side="left", padx=(0, 4))

        ctk.CTkLabel(self.time_frame, text=":", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 4))

        self.var_minute = ctk.StringVar(value=f"{self.selected_minute:02d}")
        self.combo_minute = ctk.CTkComboBox(
            self.time_frame,
            values=minutes,
            variable=self.var_minute,
            width=64,
            height=28,
            command=lambda _: self._update_preview(),
        )
        self.combo_minute.pack(side="left", padx=(0, 10))

        btn_now = ctk.CTkButton(
            self.time_frame,
            text=t("dt_btn_now"),
            width=50,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_width=1,
            command=self._set_to_now,
        )
        btn_now.pack(side="left")

        # 5. Timestamp Preview
        self.lbl_preview = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=("#2b6cb0", "#63b3ed"),
        )
        self.lbl_preview.pack(fill="x", pady=(6, 10))

        # 6. Action Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom")

        btn_apply = ctk.CTkButton(
            btn_box,
            text=t("dt_btn_apply"),
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#2b6cb0", "#3182ce"),
            hover_color=("#1a365d", "#2b6cb0"),
            height=32,
            command=self._handle_apply,
        )
        btn_apply.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_cancel = ctk.CTkButton(
            btn_box,
            text=t("dt_btn_cancel"),
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            height=32,
            command=self.destroy,
        )
        btn_cancel.pack(side="right", padx=(6, 0))

        self._on_retro_toggled()
        self._update_preview()

    def _draw_calendar_days(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        # Day of week headers (Mon .. Sun)
        weekdays_en = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        weekdays_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        headers = weekdays_de if get_current_locale() == "de" else weekdays_en

        for col, h in enumerate(headers):
            lbl = ctk.CTkLabel(
                self.cal_frame,
                text=h,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("gray40", "gray60"),
                width=42,
            )
            lbl.grid(row=0, column=col, padx=2, pady=(4, 2))

        # Calendar matrix
        cal = calendar.monthcalendar(self.selected_year, self.selected_month)
        for r_idx, week in enumerate(cal, start=1):
            for c_idx, day_num in enumerate(week):
                if day_num == 0:
                    continue

                is_selected = (day_num == self.selected_day)
                fg = ("#2b6cb0", "#3182ce") if is_selected else "transparent"
                txt_col = "white" if is_selected else ("gray15", "gray90")
                hover_col = ("#1a365d", "#2b6cb0") if is_selected else ("gray80", "gray28")

                btn = ctk.CTkButton(
                    self.cal_frame,
                    text=str(day_num),
                    width=38,
                    height=28,
                    font=ctk.CTkFont(size=11, weight="bold" if is_selected else "normal"),
                    fg_color=fg,
                    text_color=txt_col,
                    hover_color=hover_col,
                    command=lambda d=day_num: self._select_day(d),
                )
                btn.grid(row=r_idx, column=c_idx, padx=2, pady=2)

    def _select_day(self, day: int):
        self.selected_day = day
        self._draw_calendar_days()
        self._update_preview()

    def _prev_month(self):
        if self.selected_month == 1:
            self.selected_month = 12
            self.selected_year -= 1
        else:
            self.selected_month -= 1

        # Adjust day bounds
        max_days = calendar.monthrange(self.selected_year, self.selected_month)[1]
        self.selected_day = min(self.selected_day, max_days)

        self._refresh_month_label()
        self._draw_calendar_days()
        self._update_preview()

    def _next_month(self):
        if self.selected_month == 12:
            self.selected_month = 1
            self.selected_year += 1
        else:
            self.selected_month += 1

        max_days = calendar.monthrange(self.selected_year, self.selected_month)[1]
        self.selected_day = min(self.selected_day, max_days)

        self._refresh_month_label()
        self._draw_calendar_days()
        self._update_preview()

    def _refresh_month_label(self):
        month_names_en = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_names_de = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
        m_list = month_names_de if get_current_locale() == "de" else month_names_en
        self.lbl_month_year.configure(text=f"{m_list[self.selected_month]} {self.selected_year}")

    def _set_to_now(self):
        now = datetime.now(timezone(timedelta(hours=2)))
        self.selected_year, self.selected_month, self.selected_day = now.year, now.month, now.day
        self.selected_hour, self.selected_minute = now.hour, now.minute
        self.var_hour.set(f"{self.selected_hour:02d}")
        self.var_minute.set(f"{self.selected_minute:02d}")
        self._refresh_month_label()
        self._draw_calendar_days()
        self._update_preview()

    def _on_retro_toggled(self):
        is_retro = self.var_retro.get()
        if is_retro:
            self.combo_hour.configure(state="disabled")
            self.combo_minute.configure(state="disabled")
        else:
            self.combo_hour.configure(state="normal")
            self.combo_minute.configure(state="normal")
        self._update_preview()

    def _get_formatted_result(self) -> str:
        d_str = f"{self.selected_year:04d}-{self.selected_month:02d}-{self.selected_day:02d}"
        if self.var_retro.get():
            return f"{d_str} (Retroactive)"
        else:
            h = self.var_hour.get().zfill(2)
            m = self.var_minute.get().zfill(2)
            return f"{d_str} {h}:{m} CEST"

    def _update_preview(self):
        res = self._get_formatted_result()
        self.lbl_preview.configure(text=f"📌 {res}")

    def _handle_apply(self):
        final_str = self._get_formatted_result()
        is_retro = self.var_retro.get()
        if self.on_apply:
            self.on_apply(final_str, is_retro)
        self.destroy()
