import sys
import os
import json
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QRectF
from PyQt6.QtGui import QColor, QTextDocument, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView,
                             QHeaderView, QComboBox, QVBoxLayout, QMenu,
                             QStyledItemDelegate, QTextEdit, QStyleOptionViewItem, QStyle,
                             QToolBar)

DATA_DIR = "grid_notes_data"
SETTINGS_FILE = "settings.json"

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

class TextEditDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        painter.save()

        doc = QTextDocument()
        font = doc.defaultFont()
        font.setPointSize(12)
        doc.setDefaultFont(font)
        doc.setHtml(options.text)

        options.text = ""
        style = options.widget.style() if options.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter)

        painter.translate(options.rect.left() + 3, options.rect.top() + 3)
        clip = QRectF(0, 0, options.rect.width() - 6, options.rect.height() - 6)
        doc.drawContents(painter, clip)

        painter.restore()

    def createEditor(self, parent, option, index):
        return QTextEdit(parent)

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setHtml(value)

    def setModelData(self, editor, model, index):
        value = editor.toHtml()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class GridModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return 15

    def columnCount(self, parent=QModelIndex()):
        return 15

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row, col = index.row(), index.column()
        cell_index = row * 15 + col
        if cell_index >= len(self._data): return None
        cell_data = self._data[cell_index]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return cell_data.get('text', '')
        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor(cell_data.get('color', 'white'))
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid(): return False
        row, col = index.row(), index.column()
        cell_index = row * 15 + col
        if cell_index >= len(self._data): return False
        if role == Qt.ItemDataRole.EditRole:
            self._data[cell_index]['text'] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def set_color(self, index, color):
        if not index.isValid(): return
        row, col = index.row(), index.column()
        cell_index = row * 15 + col
        if cell_index >= len(self._data): return
        self._data[cell_index]['color'] = color
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def load_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GridNote Pro")
        self.setGeometry(100, 100, 1200, 800)

        self.create_menu()
        self.create_toolbar()
        self.load_data()

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.grid_switcher = QComboBox()
        self.grid_switcher.addItems(self.grid_data.keys())
        self.grid_switcher.currentIndexChanged.connect(self.switch_grid)
        main_layout.addWidget(self.grid_switcher)

        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.setItemDelegate(TextEditDelegate(self.table_view))
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

        self.grid_model = GridModel(self.grid_data[self.current_grid_id])
        self.table_view.setModel(self.grid_model)
        self.grid_model.dataChanged.connect(self.on_data_changed)

        main_layout.addWidget(self.table_view)
        self.switch_grid(0)
        self.load_settings()

    def create_menu(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        light_action = theme_menu.addAction("Light")
        light_action.triggered.connect(lambda: self.set_theme("light"))
        dark_action = theme_menu.addAction("Dark")
        dark_action.triggered.connect(lambda: self.set_theme("dark"))

    def create_toolbar(self):
        toolbar = QToolBar("Formatting")
        self.addToolBar(toolbar)
        actions = [("Bold", self.set_bold), ("Italic", self.set_italic), ("Underline", self.set_underline)]
        for name, func in actions:
            action = toolbar.addAction(name)
            action.setCheckable(True)
            action.triggered.connect(func)

    def set_bold(self, checked):
        editor = QApplication.focusWidget()
        if isinstance(editor, QTextEdit): editor.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)

    def set_italic(self, checked):
        editor = QApplication.focusWidget()
        if isinstance(editor, QTextEdit): editor.setFontItalic(checked)

    def set_underline(self, checked):
        editor = QApplication.focusWidget()
        if isinstance(editor, QTextEdit): editor.setFontUnderline(checked)

    def set_theme(self, theme_name):
        style = DARK_THEME_QSS if theme_name == "dark" else LIGHT_THEME_QSS
        self.setStyleSheet(style)
        self.save_settings(theme_name)

    def load_settings(self):
        theme = "light"
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                try:
                    settings = json.load(f)
                    theme = settings.get("theme", "light")
                except json.JSONDecodeError: pass
        self.set_theme(theme)

    def save_settings(self, theme_name):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({"theme": theme_name}, f, indent=4)

    def show_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        if not index.isValid(): return
        context_menu = QMenu(self)
        color_menu = context_menu.addMenu("Change Color")
        colors = ["White", "Red", "Green", "Blue", "Yellow"]
        for color_name in colors:
            action = color_menu.addAction(color_name)
            action.triggered.connect(lambda c=color_name.lower(), i=index: self.change_cell_color(i, c))
        context_menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def change_cell_color(self, index, color):
        self.grid_model.set_color(index, color)

    def load_data(self):
        if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
        self.grid_data = {}
        for i in range(15):
            grid_id = f"Grid {i+1}"
            file_path = os.path.join(DATA_DIR, f"grid_{i+1}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                        migrated_data = [item if isinstance(item, dict) and 'text' in item and 'color' in item else {'text': item, 'color': 'white'} for item in data]
                        while len(migrated_data) < 225: migrated_data.append({'text': '', 'color': 'white'})
                        self.grid_data[grid_id] = migrated_data[:225]
                    except (json.JSONDecodeError, TypeError):
                        self.grid_data[grid_id] = self.get_default_data()
            else:
                self.grid_data[grid_id] = self.get_default_data()
        self.current_grid_id = "Grid 1"
        self.save_all_grids()

    def get_default_data(self):
        return [{'text': f"Cell {j + 1}", 'color': 'white'} for j in range(225)]

    def save_all_grids(self):
        for grid_id, data in self.grid_data.items():
            grid_num = int(grid_id.split(' ')[1])
            file_path = os.path.join(DATA_DIR, f"grid_{grid_num}.json")
            with open(file_path, 'w') as f: json.dump(data, f, indent=4)

    def save_current_grid_data(self):
        if not hasattr(self, 'current_grid_id'): return
        grid_num = int(self.current_grid_id.split(' ')[1])
        file_path = os.path.join(DATA_DIR, f"grid_{grid_num}.json")
        with open(file_path, 'w') as f: json.dump(self.grid_data[self.current_grid_id], f, indent=4)

    def switch_grid(self, index):
        self.current_grid_id = self.grid_switcher.itemText(index)
        data = self.grid_data[self.current_grid_id]
        self.grid_model.load_data(data)
        print(f"Switched to {self.current_grid_id}")

    def on_data_changed(self, topleft, bottomright, roles):
        self.save_current_grid_data()

    def closeEvent(self, event):
        self.save_current_grid_data()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
