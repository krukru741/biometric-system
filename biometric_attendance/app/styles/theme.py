"""Application theme — color palette, design tokens, and QSS stylesheets.

All style constants live here so changing the look means editing one file.
"""
from __future__ import annotations

import pathlib

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QWidget

# ── Color palette ─────────────────────────────────────────────────────────────

# Brand
PRIMARY       = "#6B352A"   # Clay brown
PRIMARY_DARK  = "#4E2620"   # Hover/pressed
PRIMARY_LIGHT = "#8C4A3D"   # Highlights
ACCENT        = "#FFF1A6"   # Soft butter

# Semantic surface hierarchy
BACKGROUND    = "#F5F3EF"   # Off-white page background
SURFACE       = "#FFFFFF"   # Card / panel surface
SURFACE_ALT   = "#FAF9F7"   # Nested surfaces, table alternate row
SURFACE_SIDEBAR = "#5C2D23" # Sidebar (slightly darker than PRIMARY)

# Text
TEXT          = "#1E1916"   # Primary text
TEXT_SECONDARY= "#6B645F"   # Subtitles, form labels
TEXT_MUTED    = "#9B958F"   # Placeholders, captions, disabled text
TEXT_ON_PRIMARY="#FFFFFF"

# Borders
BORDER        = "#E8E4DF"   # Default border
BORDER_FOCUS  = "#6B352A"   # Focus ring
BORDER_STRONG = "#CCC8C2"   # Dividers, table header bottom

# Status Semantic Colors
SUCCESS = "#3F7D58"
SUCCESS_BG = "#EBF5EF"
WARNING = "#C58A24"
WARNING_BG = "#FEF6E4"
DANGER  = "#B94A48"
DANGER_BG  = "#FCEAEA"
INFO    = "#3A6EA8"
INFO_BG    = "#EAF0F9"


# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY = "Inter, Segoe UI, Arial, sans-serif"

# Type Scale (Sizes in px)
TS_DISPLAY          = 28
TS_PAGE_TITLE       = 22
TS_SECTION_HEADING  = 16
TS_TABLE_HEADER     = 11
TS_BODY             = 13
TS_BODY_MEDIUM      = 13
TS_CAPTION          = 11
TS_LABEL            = 12
TS_STAT_VALUE       = 32

# ── Sizing & Spacing Scale (8px-based) ──────────────────────────────────────
SIDEBAR_WIDTH = 240
TOPBAR_HEIGHT = 56

# Spacing Tokens
SPACE_XS  =  4   # Tight internal padding (icon gaps)
SPACE_SM  =  8   # Small gap (label-to-field, inline items)
SPACE_MD  = 12   # Between related items in a form row
SPACE_LG  = 16   # Content-level spacing (between fields)
SPACE_XL  = 24   # Section gap (between card sections)
SPACE_2XL = 32   # Page-level margins, card padding
SPACE_3XL = 48   # Large decorative padding

# Border Radii
RADIUS_SM   =  6   # Inputs, buttons, tags/badges
RADIUS_MD   = 10   # Cards, panels, dialogs
RADIUS_LG   = 14   # Large modal surfaces
RADIUS_PILL = 20   # Progress indicators, status chips


# ── Elevation & Helpers ─────────────────────────────────────────────────────

def load_fonts() -> None:
    """Load bundled Inter fonts into the application."""
    fonts_dir = pathlib.Path(__file__).parent.parent / "resources" / "fonts" / "Inter"
    if not fonts_dir.exists():
        return
    for font_file in fonts_dir.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))


def apply_card_shadow(widget: QWidget, level: int = 1) -> None:
    """Apply standard QGraphicsDropShadowEffect to a widget.
    
    level 1: SHADOW_CARD (Subtle card shadow)
    level 2: SHADOW_MODAL (Stronger modal/dialog shadow)
    """
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setOffset(0, 4 if level == 1 else 8)
    shadow.setBlurRadius(18 if level == 1 else 32)
    # Using a soft black with different alpha
    alpha = 20 if level == 1 else 45
    shadow.setColor(Qt.GlobalColor.black)
    
    # We must access the underlying QColor to set alpha, but Qt.black works if we construct QColor
    from PySide6.QtGui import QColor
    shadow_color = QColor(0, 0, 0, alpha)
    shadow.setColor(shadow_color)
    
    widget.setGraphicsEffect(shadow)


# ── Global QSS Stylesheet ─────────────────────────────────────────────────────

def build_global_stylesheet() -> str:
    """Return the application-wide QSS stylesheet string."""
    return f"""
/* ── Global reset ──────────────────────────────────────────────────────────── */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {TS_BODY}px;
    color: {TEXT};
    background-color: transparent;
}}

QMainWindow, QDialog, QMessageBox {{
    background-color: {BACKGROUND};
}}

QMessageBox QLabel, QDialog QLabel {{
    color: {TEXT};
    background-color: transparent;
}}

QMessageBox QPushButton {{
    background-color: {PRIMARY};
    color: {TEXT_ON_PRIMARY};
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: {SPACE_SM}px {SPACE_LG}px;
    min-width: 64px;
    font-weight: 500;
}}

QMessageBox QPushButton:hover {{
    background-color: {PRIMARY_LIGHT};
}}

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
#Sidebar {{
    background-color: {SURFACE_SIDEBAR};
    border-right: none;
}}

#SidebarAppTitle {{
    color: {TEXT_ON_PRIMARY};
    font-size: {TS_SECTION_HEADING}px;
    font-weight: 700;
    padding: {SPACE_SM}px 0px {SPACE_XS}px 0px;
}}

#SidebarAppSubtitle {{
    color: rgba(255,255,255,0.65);
    font-size: {TS_CAPTION}px;
    padding-bottom: {SPACE_SM}px;
}}

#SidebarNavButton {{
    color: rgba(255,255,255,0.85);
    background-color: transparent;
    border: none;
    border-radius: {RADIUS_SM}px;
    text-align: left;
    padding: {SPACE_SM}px {SPACE_MD}px;
    font-size: {TS_BODY_MEDIUM}px;
    font-weight: 500;
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
    border-radius: {RADIUS_SM}px;
    text-align: left;
    padding: 7px {SPACE_MD}px 7px {SPACE_MD}px;
    font-size: {TS_BODY_MEDIUM}px;
    font-weight: 500;
}}

#SidebarSubNavButton:hover {{
    background-color: rgba(255,255,255,0.10);
    color: {TEXT_ON_PRIMARY};
}}

#SidebarSubNavButton[active="true"] {{
    background-color: rgba(255,241,166,0.18);
    color: {ACCENT};
    font-weight: 600;
}}

#SidebarIndentGuide {{
    background-color: rgba(255,255,255,0.15);
    max-width: 1px;
    min-width: 1px;
}}

QPushButton#SidebarSectionHeader {{
    color: rgba(255,255,255,0.5);
    background-color: transparent;
    border: none;
    text-align: left;
    padding: {SPACE_LG}px {SPACE_MD}px {SPACE_XS}px {SPACE_MD}px;
    font-size: {TS_TABLE_HEADER}px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ── Top Bar ────────────────────────────────────────────────────────────────── */
#TopBar {{
    background-color: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}

#TopBarTitle {{
    font-size: {TS_PAGE_TITLE}px;
    font-weight: 700;
    color: {TEXT};
}}

#TopBarSubtitle {{
    font-size: {TS_BODY}px;
    color: {TEXT_SECONDARY};
}}

#TopBarUserLabel {{
    font-size: {TS_BODY_MEDIUM}px;
    color: {TEXT};
    font-weight: 600;
}}

#TopBarTimeLabel {{
    font-size: {TS_CAPTION}px;
    color: {TEXT_MUTED};
}}

/* ── Buttons ────────────────────────────────────────────────────────────────── */
QPushButton#PrimaryButton {{
    background-color: {PRIMARY};
    color: {TEXT_ON_PRIMARY};
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: 9px {SPACE_XL}px;
    font-size: {TS_BODY_MEDIUM}px;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {PRIMARY_LIGHT};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {PRIMARY_DARK};
}}

QPushButton#PrimaryButton:disabled {{
    background-color: {BORDER};
    color: {TEXT_MUTED};
}}

QPushButton#SecondaryButton {{
    background-color: {SURFACE};
    color: {PRIMARY};
    border: 1.5px solid {PRIMARY};
    border-radius: {RADIUS_SM}px;
    padding: 7px {SPACE_LG}px;
    font-size: {TS_BODY_MEDIUM}px;
    font-weight: 600;
}}

QPushButton#SecondaryButton:hover {{
    background-color: rgba(107,53,42,0.04);
}}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    padding: 6px {SPACE_MD}px;
    font-size: {TS_BODY_MEDIUM}px;
    font-weight: 500;
    border-radius: {RADIUS_SM}px;
}}

QPushButton#GhostButton:hover {{
    color: {TEXT};
    background-color: {SURFACE_ALT};
}}

QPushButton#IconButton {{
    background-color: transparent;
    border: none;
    border-radius: {RADIUS_SM}px;
    padding: {SPACE_XS}px;
}}

QPushButton#IconButton:hover {{
    background-color: {SURFACE_ALT};
}}

/* ── Inputs ─────────────────────────────────────────────────────────────────── */
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{
    background-color: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_SM}px;
    padding: 8px {SPACE_MD}px;
    font-size: {TS_BODY}px;
    color: {TEXT};
    selection-background-color: {PRIMARY_LIGHT};
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {{
    border-color: {BORDER_FOCUS};
    outline: none;
}}

QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QTimeEdit:disabled, QSpinBox:disabled {{
    background-color: {BACKGROUND};
    color: {TEXT_MUTED};
}}

QLineEdit[error="true"], QComboBox[error="true"] {{
    border-color: {DANGER};
}}

/* Checkbox */
QCheckBox {{
    spacing: {SPACE_SM}px;
    font-size: {TS_BODY}px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid {BORDER};
    background-color: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background-color: {PRIMARY};
    border-color: {PRIMARY};
    /* Could add an SVG checkmark here via image: url() if needed */
}}
QCheckBox::indicator:disabled {{
    background-color: {BACKGROUND};
    border-color: {BORDER};
}}

/* ── Labels ─────────────────────────────────────────────────────────────────── */
QLabel#ErrorLabel {{
    color: {DANGER};
    font-size: {TS_CAPTION}px;
}}

QLabel#FormLabel {{
    color: {TEXT_SECONDARY};
    font-size: {TS_LABEL}px;
    font-weight: 500;
}}

QLabel#HeadingLabel {{
    color: {TEXT};
    font-size: {TS_DISPLAY}px;
    font-weight: 700;
}}

QLabel#PageTitle {{
    color: {TEXT};
    font-size: {TS_PAGE_TITLE}px;
    font-weight: 700;
}}

QLabel#SectionHeading {{
    color: {TEXT};
    font-size: {TS_SECTION_HEADING}px;
    font-weight: 600;
}}

QLabel#SubheadingLabel {{
    color: {TEXT_SECONDARY};
    font-size: {TS_BODY}px;
}}

QLabel#StatValue {{
    color: {TEXT};
    font-size: {TS_STAT_VALUE}px;
    font-weight: 700;
}}

QLabel#StatusChip {{
    padding: {SPACE_XS}px {SPACE_SM}px;
    border-radius: {RADIUS_SM}px;
    font-size: {TS_CAPTION}px;
    font-weight: 600;
}}

/* ── Cards & Surfaces ───────────────────────────────────────────────────────── */
QFrame#Card {{
    background-color: {SURFACE};
    border-radius: {RADIUS_MD}px;
    border: 1px solid {BORDER};
}}

QFrame#Divider {{
    max-height: 1px;
    background-color: {BORDER};
}}

/* ── Tables ─────────────────────────────────────────────────────────────────── */
QTableWidget, QTableView {{
    background-color: {SURFACE};
    alternate-background-color: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    gridline-color: transparent;
    selection-background-color: rgba(107,53,42,0.08); /* PRIMARY at 8% */
    selection-color: {TEXT};
    font-size: {TS_BODY}px;
}}

QTableWidget::item, QTableView::item {{
    padding: {SPACE_SM}px;
    border-bottom: 1px solid {SURFACE_ALT};
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: rgba(107,53,42,0.04);
}}

QHeaderView::section {{
    background-color: {SURFACE_ALT};
    color: {TEXT_SECONDARY};
    font-size: {TS_TABLE_HEADER}px;
    font-weight: 600;
    text-transform: uppercase;
    padding: {SPACE_MD}px;
    border: none;
    border-bottom: 1px solid {BORDER_STRONG};
}}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD}px;
    background: {SURFACE};
    top: -1px; /* overlap with tab bar */
}}

QTabBar::tab {{
    background: {BACKGROUND};
    border: 1px solid {BORDER};
    border-bottom-color: {BORDER}; /* same as pane border */
    border-top-left-radius: {RADIUS_SM}px;
    border-top-right-radius: {RADIUS_SM}px;
    min-width: 80px;
    padding: {SPACE_SM}px {SPACE_LG}px;
    color: {TEXT_SECONDARY};
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background: {SURFACE};
    border-bottom-color: {SURFACE}; /* merge with pane */
    color: {PRIMARY};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background: {SURFACE_ALT};
}}

/* ── Scrollbars ─────────────────────────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
