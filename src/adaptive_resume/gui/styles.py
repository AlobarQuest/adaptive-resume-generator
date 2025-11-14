"""Styles - Application stylesheet definitions."""

COLORS = {
    'primary': '#2C3E50',
    'secondary': '#3498DB',
    'success': '#27AE60',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'background': '#ECF0F1',
    'text': '#2C3E50',
    'border': '#BDC3C7',
    'hover': '#3498DB',
    'disabled': '#95A5A6',
    'nav_bg': '#2C3E50',
    'nav_hover': '#34495E',
    'card_bg': '#FFFFFF',
}

APP_STYLESHEET = f"""
/* Main Window */
QMainWindow {{
    background-color: {COLORS['background']};
}}

/* Navigation Menu */
QWidget#navigationMenu {{
    background-color: {COLORS['nav_bg']};
    border-right: 1px solid {COLORS['border']};
}}

QLabel#navTitle {{
    background-color: {COLORS['nav_bg']};
    color: white;
    font-size: 14pt;
    font-weight: bold;
    padding: 15px;
}}

QFrame#navSeparator {{
    background-color: {COLORS['border']};
    max-height: 1px;
}}

QPushButton#navButton {{
    background-color: {COLORS['nav_bg']};
    color: white;
    border: none;
    border-left: 3px solid transparent;
    text-align: left;
    padding: 15px;
    font-size: 11pt;
}}

QPushButton#navButton:hover {{
    background-color: {COLORS['nav_hover']};
}}

QPushButton#navButton:checked {{
    background-color: {COLORS['secondary']};
    border-left: 3px solid white;
    font-weight: bold;
}}

/* Screen Titles */
QLabel#screenTitle {{
    font-size: 18pt;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 10px 0;
}}

QLabel#sectionTitle {{
    font-size: 14pt;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 8px 0;
}}

QLabel#panelTitle {{
    font-size: 12pt;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 5px 0;
}}

/* Hero Section */
QFrame#heroFrame {{
    background-color: {COLORS['secondary']};
    border-radius: 8px;
}}

QLabel#heroTitle {{
    color: white;
    font-size: 22pt;
    font-weight: bold;
    padding: 20px;
}}

/* Stat Cards */
QFrame#statCard {{
    background-color: {COLORS['card_bg']};
    border: 2px solid {COLORS['secondary']};
    border-radius: 8px;
    padding: 15px;
    min-width: 150px;
    min-height: 120px;
}}

QLabel#statIcon {{
    font-size: 36pt;
    padding: 5px;
    qproperty-alignment: AlignCenter;
}}

QLabel#statValue {{
    font-size: 32pt;
    font-weight: bold;
    color: {COLORS['secondary']};
    padding: 5px;
    qproperty-alignment: AlignCenter;
}}

QLabel#statLabel {{
    font-size: 10pt;
    font-weight: bold;
    color: {COLORS['text']};
    padding: 5px;
    qproperty-alignment: AlignCenter;
}}

/* Panel Frames */
QFrame#panelFrame {{
    background-color: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 15px;
}}

/* Settings Card */
QFrame#settingsCard {{
    background-color: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 15px;
}}

/* Upload Frame */
QFrame#uploadFrame {{
    background-color: {COLORS['card_bg']};
    border: 2px dashed {COLORS['border']};
    border-radius: 8px;
}}

QLabel#uploadIcon {{
    font-size: 48pt;
    color: {COLORS['disabled']};
}}

QLabel#supportedFormats {{
    color: {COLORS['disabled']};
    font-size: 9pt;
    font-style: italic;
}}

/* Preview Frame */
QFrame#previewFrame {{
    background-color: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QLabel#previewIcon {{
    font-size: 48pt;
    color: {COLORS['disabled']};
}}

/* Coming Soon Label */
QLabel#comingSoon {{
    color: {COLORS['warning']};
    font-size: 11pt;
    font-weight: bold;
    padding: 10px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['secondary']};
    color: white;
    border: none;
    padding: 8px 16px;
    font-size: 10pt;
    border-radius: 4px;
}}

QPushButton:hover {{
    background-color: {COLORS['hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['disabled']};
    color: #CCCCCC;
}}

QPushButton#primaryButton {{
    background-color: {COLORS['secondary']};
    color: white;
    font-size: 12pt;
    font-weight: bold;
    padding: 12px 24px;
    border-radius: 6px;
    min-width: 200px;
}}

QPushButton#primaryButton:hover {{
    background-color: {COLORS['hover']};
}}

/* List Widgets */
QListWidget {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 5px;
    font-size: 10pt;
}}

QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['background']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['secondary']};
    color: white;
}}

QListWidget::item:hover {{
    background-color: {COLORS['background']};
}}

/* Text Inputs */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    font-size: 10pt;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {COLORS['secondary']};
}}

/* Combo Boxes */
QComboBox {{
    background-color: white;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    font-size: 10pt;
}}

QComboBox:focus {{
    border: 2px solid {COLORS['secondary']};
}}

QComboBox::drop-down {{
    border: none;
}}

/* Splitters */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Scroll Bars */
QScrollBar:vertical {{
    border: none;
    background-color: {COLORS['background']};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['disabled']};
}}

QScrollBar:horizontal {{
    border: none;
    background-color: {COLORS['background']};
    height: 10px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border']};
    min-width: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['disabled']};
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['primary']};
    color: white;
    font-size: 9pt;
}}

/* Tool Bar */
QToolBar {{
    background-color: {COLORS['background']};
    border-bottom: 1px solid {COLORS['border']};
    spacing: 5px;
    padding: 5px;
}}

QToolBar QToolButton {{
    background-color: {COLORS['secondary']};
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
}}

QToolBar QToolButton:hover {{
    background-color: {COLORS['hover']};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    padding: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['secondary']};
    color: white;
}}

QMenu {{
    background-color: white;
    border: 1px solid {COLORS['border']};
}}

QMenu::item {{
    padding: 8px 25px 8px 20px;
}}

QMenu::item:selected {{
    background-color: {COLORS['secondary']};
    color: white;
}}
"""

def get_stylesheet():
    """Get the application stylesheet."""
    return APP_STYLESHEET
