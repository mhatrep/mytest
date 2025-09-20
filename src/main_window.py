import sys
import os
import json
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QTableView,
                             QHeaderView, QComboBox, QVBoxLayout, QMenu,
                             QTextEdit, QToolBar, QPushButton, QHBoxLayout,
                             QInputDialog, QLineEdit, QCheckBox, QLabel)
from PyQt6.QtGui import QTextDocument

from .constants import *
from .styles import LIGHT_THEME_QSS, DARK_THEME_QSS
from .delegate import TextEditDelegate
from .grid_model import GridModel
from .note_editor import NoteEditorDialog
from .hover_table_view import HoverTableView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.search_matches = []
        self.current_search_index = -1
        self.is_navigating_search = False

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

        self.table_view = HoverTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # The delegate is now only for painting, not editing
        self.table_view.setItemDelegate(TextEditDelegate(self.table_view))
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.doubleClicked.connect(self.open_note_editor)

        self.grid_model = GridModel(self.grid_data[self.current_grid_id])
        self.table_view.setModel(self.grid_model)
        self.grid_model.dataChanged.connect(self.on_data_changed)

        main_layout.addWidget(self.table_view)
        self.switch_grid(0)

    def open_note_editor(self, index):
        if not index.isValid():
            return

        cell_index = index.row() * NUM_COLS + index.column()
        current_data = self.grid_model._data[cell_index]
        title = current_data.get('title', '')
        content = current_data.get('content', '')

        dialog = NoteEditorDialog(title, content, self)
        if dialog.exec():
            new_title, new_content = dialog.get_data()
            self.grid_model.set_cell_data(index, new_title, new_content)
            self.save_current_grid_data()

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

        prev_button = QPushButton("Previous")
        prev_button.clicked.connect(self.go_to_previous_match)
        search_toolbar.addWidget(prev_button)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self.go_to_next_match)
        search_toolbar.addWidget(next_button)

        self.search_status_label = QLabel("0 / 0")
        search_toolbar.addWidget(self.search_status_label)

        self.search_case_sensitive_checkbox = QCheckBox("Case Sensitive")
        self.search_case_sensitive_checkbox.stateChanged.connect(self.perform_search)
        search_toolbar.addWidget(self.search_case_sensitive_checkbox)

        self.search_all_grids_checkbox = QCheckBox("Search all grids")
        self.search_all_grids_checkbox.stateChanged.connect(self.perform_search)
        search_toolbar.addWidget(self.search_all_grids_checkbox)

    def perform_search(self):
        if self.is_navigating_search:
            return

        search_text = self.search_input.text()
        case_sensitive = self.search_case_sensitive_checkbox.isChecked()
        search_all = self.search_all_grids_checkbox.isChecked()

        self.search_matches = []
        self.current_search_index = -1
        self.grid_model.set_highlights(set())

        if not search_text:
            self.search_status_label.setText("0 / 0")
            return

        grids_to_search = self.grid_names if search_all else [self.current_grid_id]
        temp_doc = QTextDocument()

        for grid_name in grids_to_search:
            grid_index = self.grid_names.index(grid_name)
            for i, cell_data in enumerate(self.grid_data[grid_name]):
                # Search in both title and content
                temp_doc.setHtml(cell_data.get('title', ''))
                title_text = temp_doc.toPlainText()
                temp_doc.setHtml(cell_data.get('content', ''))
                content_text = temp_doc.toPlainText()

                haystack = title_text + "\n" + content_text
                needle = search_text

                if not case_sensitive:
                    haystack = haystack.lower()
                    needle = needle.lower()

                if needle in haystack:
                    self.search_matches.append((grid_index, i))

        if self.search_matches:
            self.go_to_match(0)
        else:
            self.search_status_label.setText("0 / 0")

    def go_to_match(self, index):
        if not self.search_matches:
            return

        self.current_search_index = index
        grid_idx, cell_idx = self.search_matches[index]

        if self.grid_switcher.currentIndex() != grid_idx:
            self.is_navigating_search = True
            self.grid_switcher.setCurrentIndex(grid_idx)
            self.is_navigating_search = False

        row = cell_idx // NUM_COLS
        col = cell_idx % NUM_COLS
        model_index = self.grid_model.index(row, col)

        self.table_view.scrollTo(model_index, QTableView.ScrollHint.EnsureVisible)
        self.table_view.setCurrentIndex(model_index)
        self.grid_model.set_highlights({cell_idx})

        self.search_status_label.setText(f"{self.current_search_index + 1} / {len(self.search_matches)}")

    def go_to_previous_match(self):
        if not self.search_matches:
            return
        new_index = (self.current_search_index - 1 + len(self.search_matches)) % len(self.search_matches)
        self.go_to_match(new_index)

    def go_to_next_match(self):
        if not self.search_matches:
            return
        new_index = (self.current_search_index + 1) % len(self.search_matches)
        self.go_to_match(new_index)

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

        colors = {
            "Default (White)": "white",
            "Pastel Red": "#ffb3ba",
            "Pastel Orange": "#ffdfba",
            "Pastel Yellow": "#ffffba",
            "Pastel Green": "#baffc9",
            "Pastel Cyan": "#bafff8",
            "Pastel Blue": "#bae1ff",
            "Pastel Purple": "#e0baff",
            "Pastel Pink": "#ffbafc",
            "Pastel Brown": "#f0dcb1",
            "Pastel Gray": "#d3d3d3",
        }

        for name, hex_code in colors.items():
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(hex_code))
            icon = QIcon(pixmap)
            action = color_menu.addAction(icon, name)
            handler = partial(self.handle_color_change, index, hex_code)
            action.triggered.connect(handler)

        context_menu.addSeparator()
        copy_action = context_menu.addAction("Copy Note Content")
        copy_action.triggered.connect(lambda checked: self.copy_note_content(index))

        context_menu.addSeparator()
        group_action = context_menu.addAction("Group by Color")
        group_action.triggered.connect(self.group_by_color)
        reset_action = context_menu.addAction("Reset Grouping")
        reset_action.triggered.connect(self.reset_grouping)

        context_menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def copy_note_content(self, index):
        if not index.isValid():
            return
        cell_index = index.row() * NUM_COLS + index.column()
        cell_data = self.grid_model._data[cell_index]
        content = cell_data.get('content', '')

        # To get plain text from HTML for the clipboard
        temp_doc = QTextDocument()
        temp_doc.setHtml(content)
        plain_text = temp_doc.toPlainText()

        QApplication.clipboard().setText(plain_text)

    def handle_color_change(self, index, color, checked=False):
        """Wrapper to handle the signal from the color menu actions."""
        self.change_cell_color(index, color)

    def group_by_color(self):
        current_data = self.grid_data[self.current_grid_id]
        current_data.sort(key=lambda item: str(item.get('color', '')))
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
                            if not isinstance(item, dict):
                                item = {'text': str(item)}
                            if 'position' not in item:
                                item['position'] = pos
                            if 'content' not in item:
                                item['content'] = item.get('text', '')
                                item['title'] = f"Cell {pos + 1}"
                            if 'text' in item:
                                del item['text']
                            migrated_data.append(item)

                        while len(migrated_data) < (NUM_ROWS * NUM_COLS):
                            pos = len(migrated_data)
                            migrated_data.append(self.get_default_cell_data(pos))

                        self.grid_data[grid_name] = migrated_data[:(NUM_ROWS * NUM_COLS)]
                    except (json.JSONDecodeError, TypeError):
                        self.grid_data[grid_name] = self.get_default_data()
            else:
                self.grid_data[grid_name] = self.get_default_data()
        self.current_grid_id = self.grid_names[0]
        self.save_all_grids()

    def get_default_cell_data(self, position):
        return {'title': '', 'content': '', 'color': 'white', 'position': position}

    def get_default_data(self):
        return [self.get_default_cell_data(j) for j in range(NUM_ROWS * NUM_COLS)]

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
        if index < 0 or self.is_navigating_search:
            return
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
