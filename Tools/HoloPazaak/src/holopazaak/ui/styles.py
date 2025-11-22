from __future__ import annotations

class Theme:
    REPUBLIC = {
        "name": "Republic",
        "background": "#f0f0f0",
        "panel": "#e0e0e0",
        "text": "black",
        "button": "#4CAF50",
        "button_text": "white",
        "card_main": "#D0F0C0",
        "card_plus": "#ADD8E6",
        "card_minus": "#F08080",
        "card_flip": "#FFFFE0",
    }
    
    SITH = {
        "name": "Sith",
        "background": "#2b2b2b",
        "panel": "#3c3c3c",
        "text": "#e0e0e0",
        "button": "#800000",
        "button_text": "#e0e0e0",
        "card_main": "#405040",
        "card_plus": "#304050",
        "card_minus": "#503030",
        "card_flip": "#505030",
    }

def get_stylesheet(theme: dict[str, str]) -> str:
    return f"""
        QMainWindow {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}
        QLabel {{
            color: {theme['text']};
        }}
        QCheckBox {{
            color: {theme['text']};
        }}
        QFrame {{
            background-color: {theme['panel']};
            border-radius: 8px;
        }}
        QPushButton {{
            background-color: {theme['button']};
            color: {theme['button_text']};
            border: none;
            padding: 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {theme['button']}AA;
        }}
        QPushButton:disabled {{
            background-color: #888888;
            color: #CCCCCC;
        }}
        QTextEdit {{
            background-color: {theme['panel']};
            color: {theme['text']};
            border: 1px solid #555555;
            border-radius: 4px;
        }}
    """

