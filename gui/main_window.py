"""
Main Application Window Controller.
Manages theme settings, locale initialization, window lifecycle, and transitions between
HubView (Google Docs-style dashboard) and EditorView (Document Workspace).
"""

from __future__ import annotations
import sys
import time
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Any

from storage import StorageManager
from models import ProtocolDocument
from gui.hub_view import HubView
from gui.editor_view import EditorView
from gui.assets import ensure_icon_file
from gui.tooltip import notify_global_scroll
from i18n import (
    t,
    set_current_locale,
    get_current_locale,
)


class MainWindow(ctk.CTk):
    def __init__(self, storage: Optional[StorageManager] = None):
        super().__init__()
        self.storage = storage or StorageManager()

        # Initialize locale and appearance theme from persistent storage
        set_current_locale(self.storage.ui_locale)
        ctk.set_appearance_mode(self.storage.ui_theme)
        ctk.set_default_color_theme("blue")

        self.title(t("app_window_title"))
        self.geometry("1200x840")
        self.minsize(980, 680)

        # Set application vector icon
        try:
            icon_p = ensure_icon_file()
            if icon_p.exists():
                self._app_icon = tk.PhotoImage(file=str(icon_p))
                self.iconphoto(False, self._app_icon)
        except Exception:
            pass

        self._center_window()

        self.current_view: Optional[ctk.CTkFrame] = None
        self.active_doc: Optional[ProtocolDocument] = None

        # High-frequency scroll coalescing state
        self._last_scroll_flush_ts: float = 0.0
        self._pending_scrolls: dict[tuple[Any, str], int] = {}
        self._scroll_flush_after_id: Optional[str] = None

        self._bind_universal_mousewheel()
        self.show_hub()

    def _center_window(self):
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            w = 1200
            h = 840
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_theme = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_theme)
        self.storage.ui_theme = new_theme.lower()

    def on_language_changed(self, new_locale: str):
        self.title(t("app_window_title"))

    def show_hub(self):
        """Switches to the Google Docs-style Hub start screen."""
        if self.current_view:
            self.current_view.destroy()

        self.active_doc = None
        self.current_view = HubView(
            self,
            storage=self.storage,
            on_open_document=self.open_document,
            on_toggle_theme=self.toggle_theme,
            on_language_changed=self.on_language_changed,
        )
        self.current_view.pack(fill="both", expand=True)

    def open_document(self, doc: ProtocolDocument):
        """Switches to the Editor Workspace for the specified document."""
        if self.current_view:
            self.current_view.destroy()

        self.active_doc = doc
        self.current_view = EditorView(
            self,
            doc=doc,
            storage=self.storage,
            on_back_to_hub=self.show_hub,
        )
        self.current_view.pack(fill="both", expand=True)

    def _bind_universal_mousewheel(self):
        """
        Binds both Tcl/Tk 9.0+ <TouchpadScroll> (TIP 684 for Surface Arc Mouse & Precision Touchpads)
        and classic <MouseWheel> / X11 button scroll events globally across the application.
        """
        # Neutralize CustomTkinter's broken internal _mouse_wheel_all handler (which relies on
        # focus widget rather than hovered widget and lacks <TouchpadScroll> support)
        try:
            ctk.CTkScrollableFrame._mouse_wheel_all = lambda self_sf, event: None
        except Exception:
            pass

        # 1. Tcl/Tk 9.0+ high-precision touchpad & Surface Arc Mouse event (TIP 684)
        try:
            self.bind_all("<TouchpadScroll>", self._on_touchpad_scroll, add=True)
        except Exception:
            pass

        # 2. Standard notched mouse wheel & modifier variants (Windows, macOS, Tk 8.6/9.0)
        for seq in (
            "<MouseWheel>",
            "<Shift-MouseWheel>",
            "<Alt-MouseWheel>",
            "<Shift-Alt-MouseWheel>",
            "<Option-MouseWheel>",
            "<Shift-Option-MouseWheel>",
        ):
            try:
                self.bind_all(seq, self._on_window_mousewheel, add=True)
            except Exception:
                pass

        # 3. Linux / X11 button scroll events
        if not sys.platform.startswith("win") and sys.platform != "darwin":
            for btn in ("<Button-4>", "<Button-5>", "<Button-6>", "<Button-7>"):
                try:
                    self.bind_all(btn, self._on_window_mousewheel, add=True)
                except Exception:
                    pass

    @staticmethod
    def _has_scrollable_frame_ancestor(widget: Any) -> bool:
        """Checks whether a widget sits inside a CTkScrollableFrame."""
        curr = getattr(widget, "master", None)
        while curr is not None:
            if isinstance(curr, ctk.CTkScrollableFrame):
                return True
            curr = getattr(curr, "master", None)
        return False

    def _should_textbox_capture_scroll(self, tb_or_text: Any) -> bool:
        """
        Returns True if a CTkTextbox / tk.Text should capture scroll events itself.
        Standalone textboxes (e.g. PreviewView) always capture scroll.
        Textboxes nested inside a CTkScrollableFrame (e.g. LoggerView form_scroll)
        only capture scroll when actively focused AND possessing vertical overflow.
        """
        if not self._has_scrollable_frame_ancestor(tb_or_text):
            return True

        text_w = getattr(tb_or_text, "_textbox", tb_or_text)
        try:
            if self.focus_get() != text_w:
                return False
            y0, y1 = text_w.yview()
            if y0 <= 0.0 and y1 >= 1.0:
                return False
            return True
        except Exception:
            return False

    def _find_scrollable_container(self, widget: Any) -> Optional[Any]:
        """Walks the widget hierarchy to find the nearest active scrollable container."""
        if widget is None:
            return None

        if isinstance(widget, str):
            try:
                widget = self.nametowidget(widget)
            except Exception:
                return None

        # 1. Walk up the .master chain
        curr = widget
        while curr is not None:
            if isinstance(curr, ctk.CTkScrollableFrame):
                return curr
            if isinstance(curr, (ctk.CTkTextbox, tk.Text)):
                if self._should_textbox_capture_scroll(curr):
                    return curr
            if isinstance(curr, tk.Canvas):
                for child in getattr(curr, "winfo_children", lambda: [])():
                    if isinstance(child, ctk.CTkScrollableFrame):
                        return child
            elif isinstance(curr, ctk.CTkFrame):
                for child in getattr(curr, "winfo_children", lambda: [])():
                    if isinstance(child, tk.Canvas):
                        for gc in getattr(child, "winfo_children", lambda: [])():
                            if isinstance(gc, ctk.CTkScrollableFrame):
                                return gc
            curr = getattr(curr, "master", None)

        # 2. Check direct children if widget itself is a container holding a CTkScrollableFrame
        for child in getattr(widget, "winfo_children", lambda: [])():
            if isinstance(child, ctk.CTkScrollableFrame):
                return child
            if isinstance(child, (ctk.CTkTextbox, tk.Text)):
                if self._should_textbox_capture_scroll(child):
                    return child

        return None

    def _resolve_scroll_container(self, event) -> Optional[Any]:
        """
        3-Tier target container resolver:
        Tier 1: Hierarchy walk from event.widget (%W), matching Tcl/Tk 9.0's native pointer routing.
        Tier 2: Cursor coordinate hit-test via winfo_containing(x_root, y_root) / winfo_pointerxy().
        Tier 3: Active view fallback (scroll_docs, scroll_table, scroll_drops, form_scroll).
        """
        raw_widget = getattr(event, "widget", None)
        if isinstance(raw_widget, str):
            try:
                raw_widget = self.nametowidget(raw_widget)
            except Exception:
                raw_widget = None

        # Tier 1: Walk up from event.widget (%W) directly (immune to High-DPI coordinate scaling)
        if raw_widget is not None:
            c = self._find_scrollable_container(raw_widget)
            if c is not None:
                return c

        # Tier 2: Cursor coordinate hit-test (when event.widget is root or an outer frame)
        x_root = getattr(event, "x_root", None)
        y_root = getattr(event, "y_root", None)
        if x_root is None or y_root is None or (x_root == 0 and y_root == 0):
            try:
                x_root, y_root = self.winfo_pointerxy()
            except Exception:
                x_root, y_root = None, None

        if x_root is not None and y_root is not None:
            if raw_widget:
                try:
                    tl = raw_widget.winfo_toplevel()
                    hovered = tl.winfo_containing(x_root, y_root)
                    if hovered and hovered != tl:
                        c = self._find_scrollable_container(hovered)
                        if c is not None:
                            return c
                except Exception:
                    pass

            try:
                hovered = self.winfo_containing(x_root, y_root)
                if hovered and hovered != self:
                    c = self._find_scrollable_container(hovered)
                    if c is not None:
                        return c
            except Exception:
                pass

        # If a specific non-scrollable child control (like an outer Entry) was explicitly targeted
        # while the window is withdrawn in offscreen unit tests, do not fall through to Tier 3.
        try:
            if not self.winfo_viewable() and raw_widget is not None and raw_widget != self:
                if not isinstance(raw_widget, (HubView, EditorView)):
                    return None
        except Exception:
            pass

        # Tier 3: Active view direct target fallback (guarantees scrolling works even if
        # the cursor is over headers, margins, or DPI-scaled borders)
        if isinstance(self.current_view, HubView):
            return getattr(self.current_view, "scroll_docs", None)
        elif isinstance(self.current_view, EditorView):
            try:
                active_tab = self.current_view.tabview.get()
                if active_tab == self.current_view.tab_name_matrix:
                    return getattr(self.current_view.matrix_view, "scroll_table", None)
                elif active_tab == self.current_view.tab_name_drops:
                    lv = self.current_view.logger_view
                    scroll_drops = getattr(lv, "scroll_drops", None)
                    form_scroll = getattr(lv, "form_scroll", None)
                    if scroll_drops and x_root is not None:
                        try:
                            if x_root >= scroll_drops.winfo_rootx():
                                return scroll_drops
                        except Exception:
                            pass
                    if form_scroll and getattr(form_scroll, "_parent_canvas", None):
                        if form_scroll._parent_canvas.yview() != (0.0, 1.0):
                            return form_scroll
                    return scroll_drops or form_scroll
            except Exception:
                pass

        return None

    @staticmethod
    def _unpack_touchpad_deltas(raw_delta: int) -> tuple[int, int]:
        """
        Unpacks Tcl/Tk 9.0 <TouchpadScroll> 32-bit packed %D delta into signed 16-bit (deltaX, deltaY),
        matching ::tk::PreciseScrollDeltas in tk.tcl.
        """
        low = raw_delta & 0xFFFF
        delta_y = low if low < 0x8000 else low - 0x10000
        high = (raw_delta >> 16) & 0xFFFF
        delta_x = high if high < 0x8000 else high - 0x10000
        return delta_x, delta_y

    def _apply_canvas_scroll(self, canvas: Any, axis: str, steps: int):
        """
        Applies canvas scrolling with ~90Hz (11ms) frame-paced coalescing and synchronous
        idle redraw flushing to eliminate queue lag on heavy forms and reduce Win32 ghosting.
        """
        if steps == 0 or not canvas:
            return

        notify_global_scroll()
        now = time.perf_counter()

        # Execute immediately if outside the 11ms burst window (keeps first event & unit tests synchronous)
        if (now - self._last_scroll_flush_ts) >= 0.011 and not self._pending_scrolls:
            self._last_scroll_flush_ts = now
            try:
                if axis == "x":
                    if canvas.xview() != (0.0, 1.0):
                        canvas.xview("scroll", steps, "units")
                        canvas.update_idletasks()
                else:
                    if canvas.yview() != (0.0, 1.0):
                        canvas.yview("scroll", steps, "units")
                        canvas.update_idletasks()
            except Exception:
                pass
            return

        # Coalesce high-frequency burst events into a single per-frame flush via after_idle
        key = (canvas, axis)
        self._pending_scrolls[key] = self._pending_scrolls.get(key, 0) + steps
        if self._scroll_flush_after_id is None:
            try:
                self._scroll_flush_after_id = self.after_idle(self._flush_pending_scrolls)
            except Exception:
                self._flush_pending_scrolls()

    def _flush_pending_scrolls(self):
        self._scroll_flush_after_id = None
        self._last_scroll_flush_ts = time.perf_counter()
        pending = dict(self._pending_scrolls)
        self._pending_scrolls.clear()

        for (canvas, axis), total_steps in pending.items():
            if total_steps == 0:
                continue
            try:
                if not canvas.winfo_exists():
                    continue
                if axis == "x":
                    if canvas.xview() != (0.0, 1.0):
                        canvas.xview("scroll", total_steps, "units")
                        canvas.update_idletasks()
                else:
                    if canvas.yview() != (0.0, 1.0):
                        canvas.yview("scroll", total_steps, "units")
                        canvas.update_idletasks()
            except Exception:
                pass

    def _scroll_container_by_touchpad(self, container: ctk.CTkScrollableFrame, event):
        """Scrolls a specific CTkScrollableFrame using a Tcl/Tk 9.0 <TouchpadScroll> event."""
        canvas = getattr(container, "_parent_canvas", None)
        if not canvas:
            return

        raw_delta = int(getattr(event, "delta", 0))
        delta_x, delta_y = self._unpack_touchpad_deltas(raw_delta)
        orientation = getattr(container, "_orientation", "vertical")

        if orientation == "horizontal":
            effective = delta_x if delta_x != 0 else delta_y
            if effective != 0 and canvas.xview() != (0.0, 1.0):
                steps = -int(effective * 1.5)
                if steps == 0:
                    steps = -1 if effective > 0 else 1
                self._apply_canvas_scroll(canvas, "x", steps)
        else:
            effective = delta_y if delta_y != 0 else delta_x
            if effective != 0 and canvas.yview() != (0.0, 1.0):
                steps = -int(effective * 1.5)
                if steps == 0:
                    steps = -1 if effective > 0 else 1
                self._apply_canvas_scroll(canvas, "y", steps)

    def _scroll_container_by_wheel(self, container: ctk.CTkScrollableFrame, event):
        """Scrolls a specific CTkScrollableFrame using a <MouseWheel> or X11 button event."""
        canvas = getattr(container, "_parent_canvas", None)
        if not canvas:
            return

        orientation = getattr(container, "_orientation", "vertical")
        axis = "x" if orientation == "horizontal" else "y"

        if sys.platform.startswith("win"):
            delta = getattr(event, "delta", 0)
            if abs(delta) >= 120:
                steps = -int((delta / 120) * 35)
            else:
                steps = -int(delta * 2.5)
                if steps == 0 and delta != 0:
                    steps = -1 if delta > 0 else 1
            self._apply_canvas_scroll(canvas, axis, steps)

        elif sys.platform == "darwin":
            delta = getattr(event, "delta", 0)
            steps = -delta if delta != 0 else 0
            self._apply_canvas_scroll(canvas, axis, steps)
        else:
            num = getattr(event, "num", None)
            steps = -3 if num == 4 else 3
            self._apply_canvas_scroll(canvas, axis, steps)

    def _on_touchpad_scroll(self, event):
        """
        Handles Tcl/Tk 9.0+ <TouchpadScroll> events generated by Surface Arc Mouse
        and Windows 11 Precision Touchpads.
        """
        container = self._resolve_scroll_container(event)
        if container is None:
            return

        # Native Tkinter Text / CTkTextbox already binds <TouchpadScroll> in text.tcl
        if isinstance(container, (ctk.CTkTextbox, tk.Text)):
            return

        if isinstance(container, ctk.CTkScrollableFrame):
            self._scroll_container_by_touchpad(container, event)
            return "break"

    def _on_window_mousewheel(self, event):
        """Native parent-window scroll handler for <MouseWheel> and X11 button scroll events."""
        container = self._resolve_scroll_container(event)
        if container is None:
            return

        # If container is a CTkTextbox or Text, let native Tkinter Text handle its own scrolling
        if isinstance(container, (ctk.CTkTextbox, tk.Text)):
            return

        if isinstance(container, ctk.CTkScrollableFrame):
            self._scroll_container_by_wheel(container, event)
            return "break"

