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
}

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QListWidget#navigationList {{
    background-color: {COLORS['primary']};
    color: white;
    font-size: 11pt;
    border: none;
}}

QListWidget#navigationList::item {{
    padding: 12px;
    border-left: 3px solid transparent;
}}

QListWidget#navigationList::item:selected {{
    background-color: {COLORS['secondary']};
    border-left: 3px solid white;
}}

QPushButton {{
    background-color: {COLORS['secondary']};
    color: white;
    border: none;
    padding: 8px 16px;
    font-size: 10pt;
    border-radius: 4px;
}}

QLabel#headerLabel {{
    font-size: 16pt;
    font-weight: bold;
    color: {COLORS['primary']};
    padding: 10px 0;
}}
"""

def get_stylesheet():
    return APP_STYLESHEET
