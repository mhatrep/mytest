import sys
from PyQt6.QtCore import Qt, QItemSelectionModel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QTreeView, QDockWidget,
    QWidget, QVBoxLayout, QLineEdit, QCheckBox, QPushButton, QMenu,
)
import csv
import json
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog
from src.data_loader import load_data
from src.tree_model import TreeModel
from src.flat_proxy_model import FlatProxyModel
from src.filter_proxy_model import FilterProxyModel
from src.table_preview import TablePreviewDialog
from src.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Viewer")
        self.resize(1200, 800)
        self.settings = {
            "csv_delimiter": ",",
            "max_cell_width": 100,
            "null_format": "NULL",
            "bool_format": "True/False"
        }

        # Central Widget - Table View
        self.table_view = QTableView()
        self.table_view.setSelectionMode(self.table_view.SelectionMode.ExtendedSelection)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        self.setCentralWidget(self.table_view)

        # Menu Bar
        self._create_menu_bar()

        # Dock Widget for Tree View and Filtering
        self._create_dock_widget()

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = QMenu("&File", self)
        menu_bar.addMenu(file_menu)

        open_action = QAction("&Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        export_action = QAction("&Export", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        # Edit Menu
        edit_menu = QMenu("&Edit", self)
        menu_bar.addMenu(edit_menu)

        copy_action = QAction("&Copy", self)
        copy_action.triggered.connect(self.copy_selection)
        edit_menu.addAction(copy_action)
        self.table_view.addAction(copy_action)

        copy_path_action = QAction("Copy &Path", self)
        copy_path_action.triggered.connect(self.copy_path)
        edit_menu.addAction(copy_path_action)
        self.table_view.addAction(copy_path_action)

        edit_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)

        # View Menu
        view_menu = QMenu("&View", self)
        menu_bar.addMenu(view_menu)

        autosize_action = QAction("&Autosize Columns", self)
        autosize_action.triggered.connect(self.table_view.resizeColumnsToContents)
        view_menu.addAction(autosize_action)

        table_preview_action = QAction("Table Pre&view", self)
        table_preview_action.triggered.connect(self.show_table_preview)
        view_menu.addAction(table_preview_action)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Supported Files (*.json *.yaml *.yml *.xml);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;XML Files (*.xml)"
        )
        if file_path:
            try:
                data = load_data(file_path)
                self.source_model = TreeModel(data, settings=self.settings, source=file_path)

                self.flat_proxy_model = FlatProxyModel(self)
                self.flat_proxy_model.setSourceModel(self.source_model)

                self.filter_proxy_model = FilterProxyModel(self)
                self.filter_proxy_model.setSourceModel(self.flat_proxy_model)

                self.table_view.setModel(self.filter_proxy_model)
                self.tree_view.setModel(self.source_model)
                self.table_view.resizeColumnsToContents()

                # Sync selection
                self.tree_view.selectionModel().selectionChanged.connect(self.sync_tree_to_table)
                self.table_view.selectionModel().selectionChanged.connect(self.sync_table_to_tree)
            except Exception as e:
                print(f"Error loading file: {e}")

    def sync_tree_to_table(self, selected, deselected):
        if not selected.indexes():
            return
        source_index = selected.indexes()[0]
        proxy_index = self.flat_proxy_model.mapFromSource(source_index)
        if proxy_index.isValid():
            self.table_view.selectionModel().select(proxy_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            self.table_view.scrollTo(proxy_index, self.table_view.ScrollHint.PositionAtCenter)

    def sync_table_to_tree(self, selected, deselected):
        if not selected.indexes():
            return
        proxy_index = selected.indexes()[0]
        source_index = self.flat_proxy_model.mapToSource(proxy_index)
        if source_index.isValid():
            self.tree_view.selectionModel().select(source_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            self.tree_view.scrollTo(source_index, self.tree_view.ScrollHint.PositionAtCenter)
            # Expand the tree to the selected item
            parent = source_index.parent()
            while parent.isValid():
                self.tree_view.expand(parent)
                parent = parent.parent()

    def filter_text_changed(self, text):
        if hasattr(self, 'filter_proxy_model'):
            self.filter_proxy_model.setFilterRegularExpression(text)

    def filter_options_changed(self):
        if hasattr(self, 'filter_proxy_model'):
            case_sensitivity = Qt.CaseSensitivity.CaseSensitive if self.case_sensitive_checkbox.isChecked() else Qt.CaseSensitivity.CaseInsensitive
            use_regex = self.regex_checkbox.isChecked()
            value_only = self.filter_value_only_checkbox.isChecked()
            self.filter_proxy_model.set_filter_case_sensitivity(case_sensitivity)
            self.filter_proxy_model.set_use_regex(use_regex)
            self.filter_proxy_model.set_filter_value_only(value_only)
            # Re-apply the filter
            self.filter_proxy_model.setFilterRegularExpression(self.filter_input.text())

    def copy_selection(self):
        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        rows = sorted(list(set(index.row() for index in selection)))
        cols = sorted(list(set(index.column() for index in selection)))

        table = [[""] * len(cols) for _ in range(len(rows))]
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                index = self.table_view.model().index(row, col)
                table[i][j] = str(self.table_view.model().data(index))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(["\t".join(row) for row in table]))

    def copy_path(self):
        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        index = selection[0]
        # Path is in the second column
        path_index = self.table_view.model().index(index.row(), 1)
        path = self.table_view.model().data(path_index)

        clipboard = QApplication.clipboard()
        clipboard.setText(path)

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV (*.csv);;TSV (*.tsv);;JSON Lines (*.jsonl)"
        )
        if not file_path:
            return

        model = self.table_view.model()
        headers = [model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) for i in range(model.columnCount())]

        data = []
        for row in range(model.rowCount()):
            row_data = [model.data(model.index(row, col)) for col in range(model.columnCount())]
            data.append(dict(zip(headers, row_data)))

        try:
            with open(file_path, 'w', newline='') as f:
                if file_path.endswith('.csv'):
                    writer = csv.DictWriter(f, fieldnames=headers, delimiter=self.settings.get("csv_delimiter", ","))
                    writer.writeheader()
                    writer.writerows(data)
                elif file_path.endswith('.tsv'):
                    writer = csv.DictWriter(f, fieldnames=headers, delimiter='\t')
                    writer.writeheader()
                    writer.writerows(data)
                elif file_path.endswith('.jsonl'):
                    for row in data:
                        f.write(json.dumps(row) + '\n')
        except Exception as e:
            print(f"Error exporting data: {e}")


    def show_table_preview(self):
        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        model = self.table_view.model()
        rows = sorted(list(set(index.row() for index in selection)))
        cols = sorted(list(set(index.column() for index in selection)))

        headers = [model.headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) for c in cols]
        data = []
        for r in rows:
            row_data = [model.data(model.index(r, c)) for c in cols]
            data.append(row_data)

        dialog = TablePreviewDialog(data, headers, self)
        dialog.exec()

    def show_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.settings = dialog.get_settings()
            print("Settings saved")

    def _create_dock_widget(self):
        dock_widget = QDockWidget("Navigation and Filtering", self)
        dock_widget.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_widget)

        # Layout for the dock widget
        dock_content = QWidget()
        layout = QVBoxLayout(dock_content)

        # Filtering controls
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by value...")
        layout.addWidget(self.filter_input)

        self.case_sensitive_checkbox = QCheckBox("Match Case")
        layout.addWidget(self.case_sensitive_checkbox)

        self.regex_checkbox = QCheckBox("Use Regex")
        layout.addWidget(self.regex_checkbox)

        self.filter_value_only_checkbox = QCheckBox("Filter on Value only")
        layout.addWidget(self.filter_value_only_checkbox)

        # Connect filter controls
        self.filter_input.textChanged.connect(self.filter_text_changed)
        self.case_sensitive_checkbox.stateChanged.connect(self.filter_options_changed)
        self.regex_checkbox.stateChanged.connect(self.filter_options_changed)
        self.filter_value_only_checkbox.stateChanged.connect(self.filter_options_changed)


        # Navigation Tree
        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)

        dock_widget.setWidget(dock_content)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())