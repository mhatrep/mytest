import sys
import os
import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView,
                             QHeaderView, QComboBox, QVBoxLayout, QMenu,
                             QTextEdit, QToolBar, QPushButton, QHBoxLayout,
                             QInputDialog, QLineEdit, QCheckBox)
from PyQt6.QtGui import QTextDocument

from .constants import *
from .styles import LIGHT_THEME_QSS, DARK_THEME_QSS
from .delegate import TextEditDelegate
from .grid_model import GridModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GridNote Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.create_menu()
        self.create_toolbars()
        self.load_settings()
        self.load_data()

        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        grid_control_layout = QHBoxLayout()
        self.grid_switcher = QComboBox()
        self.grid_switcher.addItems(self.grid_names)
        self.grid_switcher.currentIndexChanged.connect(self.switch_grid)
        grid_control_layout.addWidget(self.grid_switcher)
        rename_button = QPushButton("Rename Grid")
        rename_button.clicked.connect(self.rename_grid)
        grid_control_layout.addWidget(rename_button)
        main_layout.addLayout(grid_control_layout)

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

    def create_menu(self):
        menu_bar = self.menuBar()
        view_menu = menu_bar.addMenu("View")
        theme_menu = view_menu.addMenu("Theme")
        light_action = theme_menu.addAction("Light")
        light_action.triggered.connect(lambda: self.set_theme("light"))
        dark_action = theme_menu.addAction("Dark")
        dark_action.triggered.connect(lambda: self.set_theme("dark"))

    def create_toolbars(self):
        format_toolbar = QToolBar("Formatting")
        self.addToolBar(format_toolbar)
        actions = [("Bold", self.set_bold), ("Italic", self.set_italic), ("Underline", self.set_underline)]
        for name, func in actions:
            action = format_toolbar.addAction(name)
            action.setCheckable(True)
            action.triggered.connect(func)

        search_toolbar = QToolBar("Search")
        self.addToolBar(search_toolbar)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.perform_search)
        search_toolbar.addWidget(self.search_input)
        self.search_all_grids_checkbox = QCheckBox("Search all grids")
        self.search_all_grids_checkbox.stateChanged.connect(self.perform_search)
        search_toolbar.addWidget(self.search_all_grids_checkbox)

    def perform_search(self):
        search_text = self.search_input.text().lower()
        search_all = self.search_all_grids_checkbox.isChecked()

        if not search_text:
            self.grid_model.set_highlights(set())
            return

        found_in_current_grid = set()
        grids_to_search = self.grid_names if search_all else [self.current_grid_id]
        temp_doc = QTextDocument()

        for grid_name in grids_to_search:
            for i, cell_data in enumerate(self.grid_data[grid_name]):
                temp_doc.setHtml(cell_data.get('text', ''))
                plain_text = temp_doc.toPlainText().lower()
                if search_text in plain_text:
                    if grid_name == self.current_grid_id:
                        found_in_current_grid.add(i)

        self.grid_model.set_highlights(found_in_current_grid)

    def rename_grid(self):
        current_index = self.grid_switcher.currentIndex()
        if current_index < 0: return
        current_name = self.grid_names[current_index]
        new_name, ok = QInputDialog.getText(self, "Rename Grid", "Enter new name:", text=current_name)
        if ok and new_name and new_name != current_name:
            old_key = self.grid_names[current_index]
            self.grid_names[current_index] = new_name
            self.grid_switcher.setItemText(current_index, new_name)
            self.grid_data[new_name] = self.grid_data.pop(old_key)
            self.current_grid_id = new_name
            self.save_settings()

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
        self.current_theme = theme_name
        style = DARK_THEME_QSS if theme_name == "dark" else LIGHT_THEME_QSS
        self.setStyleSheet(style)
        self.save_settings()

    def load_settings(self):
        theme = "light"
        self.grid_names = [f"Grid {i+1}" for i in range(NUM_GRIDS)]
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                try:
                    settings = json.load(f)
                    theme = settings.get("theme", "light")
                    loaded_names = settings.get("grid_names")
                    if loaded_names and len(loaded_names) == NUM_GRIDS:
                        self.grid_names = loaded_names
                except json.JSONDecodeError: pass
        self.set_theme(theme)

    def save_settings(self):
        settings = {"theme": self.current_theme, "grid_names": self.grid_names}
        with open(SETTINGS_FILE, 'w') as f: json.dump(settings, f, indent=4)

    def show_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        if not index.isValid(): return
        context_menu = QMenu(self)
        color_menu = context_menu.addMenu("Change Color")
        colors = ["White", "Red", "Green", "Blue", "Yellow"]
        for color_name in colors:
            action = color_menu.addAction(color_name)
            action.triggered.connect(lambda checked, i=index, c=color_name.lower(): self.change_cell_color(i, c))

        context_menu.addSeparator()
        group_action = context_menu.addAction("Group by Color")
        group_action.triggered.connect(self.group_by_color)
        reset_action = context_menu.addAction("Reset Grouping")
        reset_action.triggered.connect(self.reset_grouping)

        context_menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def group_by_color(self):
        current_data = self.grid_data[self.current_grid_id]
        current_data.sort(key=lambda item: item.get('color', ''))
        self.grid_model.load_data(current_data)
        self.save_current_grid_data()

    def reset_grouping(self):
        current_data = self.grid_data[self.current_grid_id]
        current_data.sort(key=lambda item: item.get('position', 0))
        self.grid_model.load_data(current_data)
        self.save_current_grid_data()

    def change_cell_color(self, index, color):
        selected_indexes = self.table_view.selectionModel().selectedIndexes()
        if index in selected_indexes:
            for selected_index in selected_indexes:
                self.grid_model.set_color(selected_index, color)
        else:
            self.grid_model.set_color(index, color)

    def load_data(self):
        if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
        self.grid_data = {}
        for i in range(NUM_GRIDS):
            grid_name = self.grid_names[i]
            file_path = os.path.join(DATA_DIR, f"grid_{i+1}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                        migrated_data = []
                        for pos, item in enumerate(data):
                            if isinstance(item, dict) and 'text' in item and 'color' in item:
                                if 'position' not in item:
                                    item['position'] = pos
                                migrated_data.append(item)
                            else:
                                migrated_data.append({'text': str(item), 'color': 'white', 'position': pos})

                        while len(migrated_data) < (NUM_ROWS * NUM_COLS):
                            pos = len(migrated_data)
                            migrated_data.append({'text': '', 'color': 'white', 'position': pos})

                        self.grid_data[grid_name] = migrated_data[:(NUM_ROWS * NUM_COLS)]
                    except (json.JSONDecodeError, TypeError):
                        self.grid_data[grid_name] = self.get_default_data()
            else:
                self.grid_data[grid_name] = self.get_default_data()
        self.current_grid_id = self.grid_names[0]
        self.save_all_grids()

    def get_default_data(self):
        return [{'text': f"Cell {j + 1}", 'color': 'white', 'position': j} for j in range(NUM_ROWS * NUM_COLS)]

    def save_all_grids(self):
        for i, grid_name in enumerate(self.grid_names):
            file_path = os.path.join(DATA_DIR, f"grid_{i+1}.json")
            with open(file_path, 'w') as f: json.dump(self.grid_data[grid_name], f, indent=4)

    def save_current_grid_data(self):
        if not hasattr(self, 'current_grid_id'): return
        current_index = self.grid_switcher.currentIndex()
        if current_index < 0: return
        file_path = os.path.join(DATA_DIR, f"grid_{current_index+1}.json")
        with open(file_path, 'w') as f: json.dump(self.grid_data[self.current_grid_id], f, indent=4)

    def switch_grid(self, index):
        if index < 0: return
        self.current_grid_id = self.grid_names[index]
        data = self.grid_data[self.current_grid_id]
        self.grid_model.load_data(data)
        self.perform_search()
        print(f"Switched to {self.current_grid_id}")

    def on_data_changed(self, topleft, bottomright, roles):
        self.save_current_grid_data()

    def closeEvent(self, event):
        self.save_current_grid_data()
        super().closeEvent(event)
