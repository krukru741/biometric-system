"""Icon helper — loads Lucide SVG icons, recolors them, returns QIcon/QPixmap.

Icons are ISC-licensed (Lucide is a fork of Feather Icons).
Source: https://lucide.dev  /  https://github.com/lucide-icons/lucide

Usage:
    from biometric_attendance.app.styles.icons import icon, pixmap
    btn.setIcon(icon("plus", color="#FFFFFF", size=16))
    lbl.setPixmap(pixmap("search", color="#6B352A", size=18))
"""
from __future__ import annotations

import pathlib
from typing import Optional

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICONS_DIR = pathlib.Path(__file__).parent.parent / "resources" / "icons"

# ── Icon name aliases ────────────────────────────────────────────────────────
# Maps semantic names used in the app → actual Lucide filenames.
ALIASES: dict[str, str] = {
    # Sidebar nav
    "dashboard":       "layout-dashboard",
    "employees":       "users",
    "departments":     "building-2",
    "positions":       "layers",
    "biometrics":      "scan",
    "enrollment":      "id-card",
    "devices":         "cpu",
    "sync":            "refresh-cw",
    "scheduling":      "calendar-days",
    "shifts":          "clock-4",
    "holidays":        "calendar",
    "schedule":        "calendar-days",
    "attendance":      "clock",
    "live":            "activity",
    "records":         "clipboard-list",
    "corrections":     "sliders-horizontal",
    "summary":         "file-text",
    "settings":        "settings",
    "admin":           "shield",
    "reports":         "file-text",
    # Actions
    "add":             "plus",
    "edit":            "pencil",
    "delete":          "trash-2",
    "archive":         "trash-2",
    "search":          "search",
    "filter":          "list-filter",
    "download":        "download",
    "upload":          "upload",
    "refresh":         "refresh-cw",
    "back":            "arrow-left",
    "more":            "ellipsis",
    "close":           "x",
    # Form
    "eye":             "eye",
    "eye-off":         "eye-off",
    "check":           "check",
    "chevron-down":    "chevron-down",
    "chevron-right":   "chevron-right",
    # Status
    "success":         "circle-check",
    "warning":         "circle-alert",
    "error":           "circle-x",
    "info":            "info",
    "online":          "wifi",
    "offline":         "wifi-off",
    # Auth
    "login":           "log-in",
    "logout":          "log-out",
    "user":            "circle-user",
    "badge":           "badge-check",
    "bell":            "bell",
    "hash":            "hash",
    "contact":         "contact",
    "scan-line":       "scan-line",
    "monitor-check":   "monitor-check",
    "map-pin":         "map-pin",
    "grip":            "grip-vertical",
    "menu":            "menu",
    "list":            "list",
    "database":        "database",
}


def _load_svg(name: str, color: str = "#292522", size: int = 18) -> Optional[QPixmap]:
    """Load an SVG by name, replace currentColor with `color`, render at `size`px."""
    import logging
    logger = logging.getLogger(__name__)

    # Resolve alias
    filename = ALIASES.get(name, name)
    svg_path = _ICONS_DIR / f"{filename}.svg"

    if not svg_path.exists():
        # Try raw name as fallback
        svg_path = _ICONS_DIR / f"{name}.svg"
        if not svg_path.exists():
            logger.warning(f"Icon not found: '{name}' (looked for '{filename}.svg')")
            return None

    svg_text = svg_path.read_text(encoding="utf-8")

    # Replace stroke color — Lucide uses currentColor
    svg_text = svg_text.replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg_text.encode()))
    if not renderer.isValid():
        logger.warning(f"Failed to render SVG for icon: '{name}'")
        return None

    px = QPixmap(QSize(size, size))
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    return px


def pixmap(name: str, color: str = "#292522", size: int = 18) -> QPixmap:
    """Return a QPixmap for the given icon name, or an empty pixmap on failure."""
    result = _load_svg(name, color=color, size=size)
    if result is None:
        empty = QPixmap(QSize(size, size))
        empty.fill(Qt.GlobalColor.transparent)
        return empty
    return result


def icon(name: str, color: str = "#292522", size: int = 18) -> QIcon:
    """Return a QIcon for the given icon name."""
    return QIcon(pixmap(name, color=color, size=size))
