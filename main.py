import sys
import sqlite3
import json
import re
import os
import concurrent.futures
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QFileDialog, QLabel, QDockWidget,
    QScrollArea, QTableWidget, QTableWidgetItem, QFrame, QAbstractItemView,
    QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QClipboard, QAction

CONFIG_FILE = "config.json"

class SearchThread(QThread):
    results_found = pyqtSignal(dict)
    search_finished = pyqtSignal()

    def __init__(self, db_paths, search_term):
        super().__init__()
        self.db_paths = db_paths
        self.search_term = search_term

    def search_database(self, db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table_tuple in tables:
                table_name = table_tuple[0]

                cursor.execute(f'PRAGMA table_info("{table_name}")')
                columns_info = cursor.fetchall()
                column_names = [info[1] for info in columns_info]

                if not column_names:
                    continue

                where_clauses = [f'LOWER("{col}") LIKE LOWER(?)' for col in column_names]
                where_statement = " OR ".join(where_clauses)
                query = f'SELECT * FROM "{table_name}" WHERE {where_statement}'

                search_params = (f'%{self.search_term}%',) * len(column_names)

                rows = cursor.execute(query, search_params).fetchall()

                if rows:
                    result_data = {
                        "db_path": db_path,
                        "table_name": table_name,
                        "headers": column_names,
                        "rows": rows,
                        "search_term": self.search_term
                    }
                    self.results_found.emit(result_data)

        except sqlite3.Error as e:
            table_name_for_error = table_tuple[0] if 'table_tuple' in locals() else 'N/A'
            print(f"Error processing table '{table_name_for_error}' in {db_path}: {e}")
        finally:
            if conn:
                conn.close()

    def run(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.search_database, self.db_paths)
        self.search_finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite Search")
        self.databases = []
        self.search_thread = None
        self.searching_label = None
        self.result_tables = {}

        # Central Widget (Right Pane)
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")

        search_actions_layout = QHBoxLayout()
        self.search_button = QPushButton("Search")
        self.copy_button = QPushButton("Copy All Results")
        self.save_button = QPushButton("Save Results")
        search_actions_layout.addWidget(self.search_button)
        search_actions_layout.addWidget(self.copy_button)
        search_actions_layout.addWidget(self.save_button)

        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_layout.setSpacing(10)
        self.results_area.setWidget(self.results_container)

        right_layout.addWidget(QLabel("Search Term:"))
        right_layout.addWidget(self.search_input)
        right_layout.addLayout(search_actions_layout)
        right_layout.addWidget(QLabel("Results:"))
        right_layout.addWidget(self.results_area)
        self.setCentralWidget(right_pane)

        # Dock Widget (Left Pane)
        self.db_dock_widget = QDockWidget("Databases", self)
        self.db_dock_widget.setObjectName("DatabasesDockWidget")
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)

        db_button_layout = QHBoxLayout()
        self.add_db_button = QPushButton("Add")
        self.remove_db_button = QPushButton("Remove")
        db_button_layout.addWidget(self.add_db_button)
        db_button_layout.addWidget(self.remove_db_button)

        self.db_list_widget = QListWidget()
        left_layout.addLayout(db_button_layout)
        left_layout.addWidget(QLabel("Selected Databases:"))
        left_layout.addWidget(self.db_list_widget)

        self.show_full_path_checkbox = QCheckBox("Show Full Path")
        left_layout.addWidget(self.show_full_path_checkbox)

        self.db_dock_widget.setWidget(left_pane)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.db_dock_widget)

        # Toolbar
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolBar")
        self.toggle_db_panel_action = QAction("Databases", self)
        self.toggle_db_panel_action.setCheckable(True)
        self.toggle_db_panel_action.triggered.connect(self.toggle_db_panel)
        toolbar.addAction(self.toggle_db_panel_action)

        # Connections
        self.db_dock_widget.visibilityChanged.connect(self.toggle_db_panel_action.setChecked)
        self.add_db_button.clicked.connect(self.add_databases)
        self.remove_db_button.clicked.connect(self.remove_database)
        self.search_button.clicked.connect(self.start_search)
        self.search_input.returnPressed.connect(self.start_search)
        self.copy_button.clicked.connect(self.copy_all_results_to_clipboard)
        self.save_button.clicked.connect(self.save_results_to_file)
        self.db_list_widget.itemChanged.connect(self.on_db_item_changed)
        self.show_full_path_checkbox.stateChanged.connect(self.update_db_list_display)


        self.load_config()
        self.populate_db_list()

        self.db_dock_widget.setVisible(False)

    def toggle_db_panel(self, checked):
        self.db_dock_widget.setVisible(checked)

    def on_db_item_changed(self, item):
        self.save_config()

    def update_db_list_display(self):
        self.populate_db_list()
        self.save_config()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.databases = config.get("databases", [])
                self.show_full_path_checkbox.setChecked(config.get("show_full_path", False))

                geometry = config.get("window_geometry")
                if geometry:
                    self.restoreGeometry(bytes.fromhex(geometry))

                state = config.get("window_state")
                if state:
                    self.restoreState(bytes.fromhex(state))

        except (FileNotFoundError, json.JSONDecodeError):
            self.databases = []
            self.resize(800, 600)

    def save_config(self):
        current_databases = []
        for i in range(self.db_list_widget.count()):
            item = self.db_list_widget.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            current_databases.append({
                "path": path,
                "checked": item.checkState() == Qt.CheckState.Checked
            })

        config = {
            "databases": current_databases,
            "show_full_path": self.show_full_path_checkbox.isChecked(),
            "window_geometry": self.saveGeometry().toHex().data().decode(),
            "window_state": self.saveState().toHex().data().decode()
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def populate_db_list(self):
        self.db_list_widget.blockSignals(True)
        self.db_list_widget.clear()
        show_full_path = self.show_full_path_checkbox.isChecked()
        for db in self.databases:
            path = db["path"]
            display_text = path if show_full_path else os.path.basename(path)
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if db.get("checked", True) else Qt.CheckState.Unchecked)
            self.db_list_widget.addItem(item)
        self.db_list_widget.blockSignals(False)

    def add_databases(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select SQLite Databases", "", "SQLite Databases (*.db *.sqlite *.sqlite3)")
        if files:
            added = False
            existing_paths = [db["path"] for db in self.databases]
            for file in files:
                if file not in existing_paths:
                    self.databases.append({"path": file, "checked": True})
                    added = True
            if added:
                self.populate_db_list()
                self.save_config()

    def remove_database(self):
        selected_items = self.db_list_widget.selectedItems()
        if not selected_items:
            return

        paths_to_remove = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}
        self.databases = [db for db in self.databases if db["path"] not in paths_to_remove]

        self.populate_db_list()
        self.save_config()

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def start_search(self):
        search_term = self.search_input.text()

        checked_db_paths = []
        for i in range(self.db_list_widget.count()):
            item = self.db_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                path = item.data(Qt.ItemDataRole.UserRole)
                checked_db_paths.append(path)

        if not search_term or not checked_db_paths:
            return

        self.search_button.setEnabled(False)
        self._clear_layout(self.results_layout)
        self.result_tables.clear()

        self.searching_label = QLabel("Searching...")
        self.results_layout.addWidget(self.searching_label)

        self.search_thread = SearchThread(checked_db_paths, search_term)
        self.search_thread.results_found.connect(self.add_result_batch)
        self.search_thread.search_finished.connect(self.on_search_finished)
        self.search_thread.start()

    def add_result_batch(self, result_data):
        if self.searching_label:
            self.searching_label.deleteLater()
            self.searching_label = None

        db_path = result_data['db_path']
        table_name = result_data['table_name']
        search_term = result_data['search_term']
        table_key = (db_path, table_name)

        if table_key not in self.result_tables:
            show_full_path = self.show_full_path_checkbox.isChecked()
            display_db_path = db_path if show_full_path else os.path.basename(db_path)
            info_label = QLabel(f"<b>Database:</b> {display_db_path} &nbsp;&nbsp; <b>Table:</b> {table_name}")
            info_label.setTextFormat(Qt.TextFormat.RichText)
            self.results_layout.addWidget(info_label)

            table = QTableWidget()
            headers = result_data['headers']
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

            self.results_layout.addWidget(table)
            self.result_tables[table_key] = table

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            self.results_layout.addWidget(separator)
        else:
            table = self.result_tables[table_key]

        rows = result_data['rows']
        start_row = table.rowCount()
        table.setRowCount(start_row + len(rows))
        for row_index, row_data in enumerate(rows):
            row_position = start_row + row_index
            for col_index, cell_data in enumerate(row_data):
                cell_text = str(cell_data)
                label = QLabel()
                label.setWordWrap(True)
                if search_term.lower() in cell_text.lower():
                    # Use regex for case-insensitive replacement
                    pattern = re.compile(re.escape(search_term), re.IGNORECASE)
                    highlighted_text = pattern.sub(f"<span style='background-color: yellow;'>\\g<0></span>", cell_text)
                    label.setText(highlighted_text)
                else:
                    label.setText(cell_text)
                table.setCellWidget(row_position, col_index, label)


    def on_search_finished(self):
        if self.searching_label:
            self.searching_label.setText("No matches found.")

        for table in self.result_tables.values():
            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            content_height = sum(table.rowHeight(i) for i in range(table.rowCount()))
            total_height = table.horizontalHeader().height() + content_height + (table.frameWidth() * 2)
            table.setFixedHeight(total_height)

        self.search_button.setEnabled(True)

    def _get_formatted_results(self):
        if not self.result_tables:
            return "No results to export."

        full_text = []
        sorted_table_keys = sorted(self.result_tables.keys())

        for key in sorted_table_keys:
            db_path, table_name = key
            table = self.result_tables[key]

            full_text.append(f"Database: {db_path}   Table: {table_name}")

            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
            rows_data = []
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    widget = table.cellWidget(row, col)
                    if widget and isinstance(widget, QLabel):
                        # Strip HTML tags for clean export
                        clean_text = re.sub('<[^<]+?>', '', widget.text())
                        row_data.append(clean_text)
                    else:
                        item = table.item(row, col)
                        row_data.append(item.text() if item else "")
                rows_data.append(row_data)

            if not headers and not rows_data:
                continue

            column_widths = [len(h) for h in headers]
            for row_data in rows_data:
                for i, cell in enumerate(row_data):
                    if i < len(column_widths):
                        column_widths[i] = max(column_widths[i], len(cell))
                    else:
                        column_widths.append(len(cell))

            header_line = " | ".join(header.ljust(width) for header, width in zip(headers, column_widths))
            full_text.append(header_line)

            separator_line = "-+-".join("-" * width for width in column_widths)
            full_text.append(separator_line)

            for row_data in rows_data:
                row_line = " | ".join(cell.ljust(width) for cell, width in zip(row_data, column_widths))
                full_text.append(row_line)

            full_text.append("\n" + "="*80 + "\n")

        return "\n".join(full_text)

    def copy_all_results_to_clipboard(self):
        results_text = self._get_formatted_results()
        if not self.result_tables:
            return

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(results_text)

    def save_results_to_file(self):
        results_text = self._get_formatted_results()
        if not self.result_tables:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Results", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(results_text)
            except IOError as e:
                print(f"Error saving file: {e}")

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())