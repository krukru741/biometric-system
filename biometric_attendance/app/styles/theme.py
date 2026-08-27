"""Application theme — color palette and QSS stylesheets.

Colors from 01-UI-UX-STRUCTURE.md §4.
All style constants live here so changing the look means editing one file.
"""
from __future__ import annotations

# ── Color palette ─────────────────────────────────────────────────────────────
PRIMARY = "#6B352A"          # Clay brown — sidebar background, primary actions
PRIMARY_DARK = "#4E2620"     # Darker clay for hover/pressed states
PRIMARY_LIGHT = "#8C4A3D"    # Lighter clay for highlights
ACCENT = "#FFF1A6"           # Soft butter — active nav item highlight, badges
BACKGROUND = "#F8F7F4"       # Off-white page background
SURFACE = "#FFFFFF"          # Card / panel surface
TEXT = "#292522"             # Primary text
TEXT_ON_PRIMARY = "#FFFFFF"  # Text on clay-brown surfaces
MUTED = "#77716C"            # Secondary / placeholder text
BORDER = "#E2DDD8"           # Subtle border
SUCCESS = "#3F7D58"          # Green for present/active
WARNING = "#C58A24"          # Amber for late/pending
DANGER = "#B94A48"           # Red for absent/error
INFO = "#3A6EA8"             # Blue for informational


# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI, Inter, Arial, sans-serif"
FONT_SIZE_BASE = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_LARGE = 15
FONT_SIZE_TITLE = 22
FONT_SIZE_HEADING = 18


# ── Sizing ────────────────────────────────────────────────────────────────────
SIDEBAR_WIDTH = 220
TOPBAR_HEIGHT = 52
BORDER_RADIUS = 8
CARD_BORDER_RADIUS = 10
BUTTON_BORDER_RADIUS = 6
INPUT_BORDER_RADIUS = 6


def build_global_stylesheet() -> str:
    """Return the application-wide QSS stylesheet string."""
    return f"""
/* ── Global reset ──────────────────────────────────────────────────────────── */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BASE}px;
    color: {TEXT};
    background-color: transparent;
}}

QMainWindow {{
    background-color: {BACKGROUND};
}}

QDialog {{
    background-color: {BACKGROUND};
}}

QMessageBox {{
    background-color: {BACKGROUND};
}}

QMessageBox QLabel {{
    color: {TEXT};
    background-color: transparent;
}}

QDialog QLabel {{
    color: {TEXT};
    background-color: transparent;
}}

QMessageBox QPushButton {{
    background-color: {PRIMARY};
    color: {TEXT_ON_PRIMARY};
    border: none;
    border-radius: {BUTTON_BORDER_RADIUS}px;
    padding: 6px 18px;
    min-width: 64px;
}}

QMessageBox QPushButton:hover {{
    background-color: {PRIMARY_LIGHT};
}}

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
#Sidebar {{
    background-color: {PRIMARY};
    border-right: none;
}}

#SidebarAppTitle {{
    color: {TEXT_ON_PRIMARY};
    font-size: {FONT_SIZE_LARGE}px;
    font-weight: 700;
    padding: 8px 0px 4px 0px;
}}

#SidebarAppSubtitle {{
    color: rgba(255,255,255,0.65);
    font-size: {FONT_SIZE_SMALL}px;
    padding-bottom: 8px;
}}

#SidebarNavButton {{
    color: rgba(255,255,255,0.85);
    background-color: transparent;
    border: none;
    border-radius: {BORDER_RADIUS}px;
    text-align: left;
    padding: 9px 14px;
    font-size: {FONT_SIZE_BASE}px;
}}

#SidebarNavButton:hover {{
    background-color: rgba(255,255,255,0.12);
    color: {TEXT_ON_PRIMARY};
}}

#SidebarNavButton[active="true"] {{
    background-color: {ACCENT};
    color: {PRIMARY};
    font-weight: 600;
}}

/* ── Sidebar submenu items ─────────────────────────────────────────────── */
#SidebarSubNavButton {{
    color: rgba(255,255,255,0.7);
    background-color: transparent;
    border: none;
    border-radius: {BORDER_RADIUS}px;
    text-align: left;
    padding: 7px 14px 7px 10px;
    font-size: {FONT_SIZE_SMALL}px;
}}

#SidebarSubNavButton:hover {{
    background-color: rgba(255,255,255,0.10);
    color: {TEXT_ON_PRIMARY};
}}

#SidebarSubNavButton[active="true"] {{
    background-color: rgba(255,241,166,0.18);
    color: {ACCENT};
    font-weight: 600;
    border-left: 2px solid {ACCENT};
    padding-left: 8px;
}}

#SidebarIndentGuide {{
    background-color: rgba(255,255,255,0.15);
    max-width: 1px;
    min-width: 1px;
}}

QPushButton#SidebarSectionHeader {{
    color: rgba(255,255,255,0.6);
    background-color: transparent;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 10px 14px 2px 14px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QPushButton#SidebarSectionHeader:hover {{
    color: #FFFFFF;
}}

/* ── Top Bar ────────────────────────────────────────────────────────────────── */
#TopBar {{
    background-color: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}

#TopBarTitle {{
    font-size: {FONT_SIZE_HEADING}px;
    font-weight: 700;
    color: {TEXT};
}}

#TopBarSubtitle {{
    font-size: {FONT_SIZE_SMALL}px;
    color: {MUTED};
}}

#TopBarUserLabel {{
    font-size: {FONT_SIZE_BASE}px;
    color: {TEXT};
    font-weight: 500;
}}

#TopBarTimeLabel {{
    font-size: {FONT_SIZE_SMALL}px;
    color: {MUTED};
}}

/* ── Buttons ────────────────────────────────────────────────────────────────── */
QPushButton#PrimaryButton {{
    background-color: {PRIMARY};
    color: {TEXT_ON_PRIMARY};
    border: none;
    border-radius: {BUTTON_BORDER_RADIUS}px;
    padding: 9px 20px;
    font-size: {FONT_SIZE_BASE}px;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {PRIMARY_LIGHT};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {PRIMARY_DARK};
}}

QPushButton#PrimaryButton:disabled {{
    background-color: {MUTED};
    color: rgba(255,255,255,0.5);
}}

QPushButton#SecondaryButton {{
    background-color: transparent;
    color: {PRIMARY};
    border: 1.5px solid {PRIMARY};
    border-radius: {BUTTON_BORDER_RADIUS}px;
    padding: 8px 20px;
    font-size: {FONT_SIZE_BASE}px;
    font-weight: 500;
}}

QPushButton#SecondaryButton:hover {{
    background-color: rgba(107,53,42,0.07);
}}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {MUTED};
    border: none;
    padding: 6px 12px;
    font-size: {FONT_SIZE_SMALL}px;
}}

QPushButton#GhostButton:hover {{
    color: {TEXT};
    text-decoration: underline;
}}

/* ── Inputs ─────────────────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {SURFACE};
    border: 1.5px solid {BORDER};
    border-radius: {INPUT_BORDER_RADIUS}px;
    padding: 8px 12px;
    font-size: {FONT_SIZE_BASE}px;
    color: {TEXT};
    selection-background-color: {PRIMARY_LIGHT};
}}

QLineEdit:focus {{
    border-color: {PRIMARY};
    outline: none;
}}

QLineEdit:disabled {{
    background-color: {BACKGROUND};
    color: {MUTED};
}}

QLineEdit[error="true"] {{
    border-color: {DANGER};
}}

/* ── Labels ─────────────────────────────────────────────────────────────────── */
QLabel#ErrorLabel {{
    color: {DANGER};
    font-size: {FONT_SIZE_SMALL}px;
}}

QLabel#FormLabel {{
    color: {TEXT};
    font-size: {FONT_SIZE_BASE}px;
    font-weight: 500;
}}

QLabel#HeadingLabel {{
    color: {TEXT};
    font-size: {FONT_SIZE_TITLE}px;
    font-weight: 700;
}}

QLabel#SubheadingLabel {{
    color: {MUTED};
    font-size: {FONT_SIZE_BASE}px;
}}

/* ── Cards ──────────────────────────────────────────────────────────────────── */
QFrame#Card {{
    background-color: {SURFACE};
    border-radius: {CARD_BORDER_RADIUS}px;
    border: 1px solid {BORDER};
}}

/* ── Scrollbars ─────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {MUTED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
