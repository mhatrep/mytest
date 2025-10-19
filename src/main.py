import sys
from PyQt6.QtCore import Qt, QItemSelectionModel
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QDockWidget,
    QWidget, QVBoxLayout, QLineEdit, QCheckBox, QPushButton, QMenu, QComboBox,
)
import csv
import json
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog
from src.data_loader import load_data
from src.filter_proxy_model import FilterProxyModel
from src.table_preview import TablePreviewDialog
from src.pandas_model import PandasModel
from src.settings_dialog import SettingsDialog
from src.table_delegate import TableInCellDelegate

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
        self.table_view.setItemDelegate(TableInCellDelegate(self.table_view))
        self.setCentralWidget(self.table_view)

        # Menu Bar
        self._create_menu_bar()

        # Filtering controls
        self._create_filtering_controls()

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
                self.dataframes = load_data(file_path)
                self.table_selector.clear()
                self.table_selector.addItems(self.dataframes.keys())

                if self.dataframes:
                    self.display_selected_table(list(self.dataframes.keys())[0])

            except Exception as e:
                print(f"Error loading file: {e}")

    def display_selected_table(self, table_path):
        if table_path in self.dataframes:
            df = self.dataframes[table_path]
            self.pandas_model = PandasModel(df)
            self.filter_proxy_model = FilterProxyModel(self)
            self.filter_proxy_model.setSourceModel(self.pandas_model)
            self.table_view.setModel(self.filter_proxy_model)
            self.table_view.resizeColumnsToContents()
            self.table_view.resizeRowsToContents()

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
        if not hasattr(self, 'pandas_model') or self.pandas_model._data.empty:
            return

        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        df = self.pandas_model._data
        selected_rows = sorted(list(set(index.row() for index in selection)))
        selected_cols = sorted(list(set(index.column() for index in selection)))

        sub_df = df.iloc[selected_rows, selected_cols]
        clipboard = QApplication.clipboard()
        clipboard.setText(sub_df.to_csv(sep='\t', index=False, header=True))

    def export_data(self):
        if not hasattr(self, 'pandas_model') or self.pandas_model._data.empty:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "CSV (*.csv);;TSV (*.tsv);;JSON Lines (*.jsonl)"
        )
        if not file_path:
            return

        df = self.pandas_model._data
        try:
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, sep=self.settings.get("csv_delimiter", ","))
            elif file_path.endswith('.tsv'):
                df.to_csv(file_path, index=False, sep='\t')
            elif file_path.endswith('.jsonl'):
                df.to_json(file_path, orient='records', lines=True)
        except Exception as e:
            print(f"Error exporting data: {e}")


    def show_table_preview(self):
        if not hasattr(self, 'pandas_model') or self.pandas_model._data.empty:
            return

        selection = self.table_view.selectionModel().selectedIndexes()
        if not selection:
            return

        df = self.pandas_model._data
        selected_rows = sorted(list(set(index.row() for index in selection)))
        selected_cols = sorted(list(set(index.column() for index in selection)))

        sub_df = df.iloc[selected_rows, selected_cols]
        headers = sub_df.columns.tolist()
        data = sub_df.values.tolist()

        dialog = TablePreviewDialog(data, headers, self)
        dialog.exec()

    def show_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec():
            self.settings = dialog.get_settings()
            print("Settings saved")

    def _create_filtering_controls(self):
        # A new toolbar for filtering controls
        toolbar = self.addToolBar("Filtering")

        self.table_selector = QComboBox()
        self.table_selector.currentTextChanged.connect(self.display_selected_table)
        toolbar.addWidget(self.table_selector)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by value...")
        self.filter_input.textChanged.connect(self.filter_text_changed)
        toolbar.addWidget(self.filter_input)

        self.case_sensitive_checkbox = QCheckBox("Match Case")
        self.case_sensitive_checkbox.stateChanged.connect(self.filter_options_changed)
        toolbar.addWidget(self.case_sensitive_checkbox)

        self.regex_checkbox = QCheckBox("Use Regex")
        self.regex_checkbox.stateChanged.connect(self.filter_options_changed)
        toolbar.addWidget(self.regex_checkbox)

        self.filter_value_only_checkbox = QCheckBox("Filter on Value only")
        self.filter_value_only_checkbox.stateChanged.connect(self.filter_options_changed)
        toolbar.addWidget(self.filter_value_only_checkbox)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())