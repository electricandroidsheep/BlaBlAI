"""
Asset and branding generator for BlaBlAI.
Generates crisp, high-resolution icons for window chrome, hub, and editor headers
using PIL without requiring external image files.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import customtkinter as ctk

_CACHED_ICON_IMAGES = {}
_CACHED_ICON_PATH: Optional[Path] = None


def generate_blablai_icon(size: int = 128) -> Image.Image:
    """
    Renders a modern, vibrant vector-like icon for BlaBlAI:
    A curved chat bubble with gradient-like blue fill, featuring an academic cap / spark motif
    and stylized letter 'B'.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer padding
    pad = int(size * 0.08)
    radius = int(size * 0.24)

    # 1. Main background bubble (rounded rectangle)
    bbox = [pad, pad, size - pad, size - pad]
    # Primary royal blue #2B6CB0
    draw.rounded_rectangle(bbox, radius=radius, fill=(43, 108, 176, 255))

    # 2. Subtle top-highlight for 3D depth
    highlight_bbox = [pad + 2, pad + 2, size - pad - 2, int(size * 0.52)]
    draw.rounded_rectangle(highlight_bbox, radius=int(radius * 0.9), fill=(49, 130, 206, 120))

    # 3. Speech bubble notch/tail on bottom-left
    tail_x1 = int(size * 0.22)
    tail_y1 = size - pad - 2
    tail_x2 = int(size * 0.38)
    tail_y2 = size - pad - 2
    tail_peak_x = int(size * 0.16)
    tail_peak_y = int(size * 0.96)
    draw.polygon([(tail_x1, tail_y1), (tail_x2, tail_y2), (tail_peak_x, tail_peak_y)], fill=(43, 108, 176, 255))

    # 4. Stylized Academic Cap / Diamond Sparkle on top
    cap_cx = int(size * 0.50)
    cap_cy = int(size * 0.46)
    cw = int(size * 0.24)
    ch = int(size * 0.14)

    # Diamond graduation top
    poly = [
        (cap_cx, cap_cy - ch),
        (cap_cx + cw, cap_cy),
        (cap_cx, cap_cy + ch),
        (cap_cx - cw, cap_cy),
    ]
    draw.polygon(poly, fill=(255, 255, 255, 245))

    # Cap base / ribbon
    skull_bbox = [cap_cx - int(cw * 0.55), cap_cy + int(ch * 0.2), cap_cx + int(cw * 0.55), cap_cy + int(ch * 1.5)]
    draw.ellipse(skull_bbox, fill=(226, 232, 240, 240))

    # Tassel thread & bead
    draw.line([(cap_cx + cw, cap_cy), (cap_cx + cw + 4, cap_cy + int(ch * 1.3))], fill=(246, 224, 94, 255), width=max(2, int(size * 0.025)))
    draw.ellipse([cap_cx + cw + 2, cap_cy + int(ch * 1.2), cap_cx + cw + 6, cap_cy + int(ch * 1.6)], fill=(246, 224, 94, 255))

    # AI sparkle / node accents
    s_size = max(2, int(size * 0.04))
    sparkle_x = int(size * 0.72)
    sparkle_y = int(size * 0.26)
    draw.ellipse([sparkle_x - s_size, sparkle_y - s_size, sparkle_x + s_size, sparkle_y + s_size], fill=(246, 224, 94, 255))

    return img


_CACHED_PIL_ICON: Optional[Image.Image] = None


def get_blablai_ctk_image(size: tuple[int, int] = (32, 32)) -> ctk.CTkImage:
    """Returns a CTkImage of the BlaBlAI icon at the requested size."""
    global _CACHED_PIL_ICON
    if _CACHED_PIL_ICON is None:
        _CACHED_PIL_ICON = generate_blablai_icon(128)

    return ctk.CTkImage(light_image=_CACHED_PIL_ICON, dark_image=_CACHED_PIL_ICON, size=size)


def ensure_icon_file(dest_dir: Optional[Path] = None) -> Path:
    """Generates and persists blablai_icon.png to disk for OS window icons."""
    global _CACHED_ICON_PATH
    if _CACHED_ICON_PATH and _CACHED_ICON_PATH.exists():
        return _CACHED_ICON_PATH

    target_dir = dest_dir or Path(__file__).parent.parent
    icon_path = target_dir / "blablai_icon.png"
    if not icon_path.exists():
        img = generate_blablai_icon(256)
        img.save(icon_path, format="PNG")
    _CACHED_ICON_PATH = icon_path
    return icon_path
