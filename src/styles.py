LIGHT_THEME_QSS = """
    QWidget { background-color: #f0f0f0; color: #000; }
    QTableView { background-color: #fff; color: #000; alternate-background-color: #f5f5f5; gridline-color: #dcdcdc; }
    QHeaderView::section { background-color: #e8e8e8; color: #000; }
    QToolBar { background-color: #f0f0f0; border: none; }
    QComboBox, QMenu { background-color: #fff; color: #000; }
    QComboBox::drop-down { border: none; }
    QMainWindow { background-color: #f0f0f0; }
    QMenu::item:selected { background-color: #dcdcdc; }
"""

DARK_THEME_QSS = """
    QWidget { background-color: #2b2b2b; color: #f0f0f0; }
    QTableView { background-color: #3c3c3c; color: #f0f0f0; alternate-background-color: #4a4a4a; gridline-color: #555; }
    QHeaderView::section { background-color: #555; color: #f0f0f0; border: 1px solid #666; }
    QToolBar { background-color: #333; border: none; }
    QComboBox, QMenu { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; }
    QComboBox::drop-down { border: none; }
    QMainWindow { background-color: #2b2b2b; }
    QMenu::item:selected { background-color: #555; }
"""
