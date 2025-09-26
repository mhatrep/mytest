import sys
import os
import pandas as pd
import webbrowser
import tempfile
import subprocess
import traceback
from PyQt6.QtCore import QSortFilterProxyModel, Qt, QObject, QThread, pyqtSignal, QAbstractTableModel
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStatusBar, QToolBar,
                             QTableView, QFileDialog, QLineEdit, QVBoxLayout,
                             QWidget, QDialog, QTextEdit, QMessageBox,
                             QComboBox, QPushButton, QFormLayout, QCheckBox, QTabWidget,
                             QSpinBox, QLabel, QInputDialog, QHBoxLayout)
from PyQt6.QtGui import QAction
from table_model import PandasModel
from reporter import generate_recommendations
import profilers
import exporter
import grain_finder
import hierarchy_finder
import key_detector
import query_generator


class KeyDetectorOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detect Keys Options")
        self.layout = QFormLayout(self)
        # Options will be added in a later phase
        self.ok_button = QPushButton("Run Analysis")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def get_options(self):
        # To be expanded in later phases
        return {}


class QueryReportDialog(QDialog):
    def __init__(self, query_string: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generated SQL Queries")
        self.setGeometry(200, 200, 700, 500)
        self.layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(query_string)
        self.text_edit.setFontFamily("Courier")
        self.layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.close_button)
        self.layout.addLayout(button_layout)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        if self.parent() and hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage("Queries copied to clipboard!", 3000)


class KeyDetectorReportDialog(QDialog):
    def __init__(self, result_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Primary Key Candidate Report")
        self.setGeometry(150, 150, 800, 600)
        self.layout = QVBoxLayout(self)

        total_rows = result_data.get("total_rows", "N/A")
        self.summary_label = QLabel(f"<b>Total Rows Scanned:</b> {total_rows}")
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.layout.addWidget(self.summary_label)

        self.table_view = QTableView()
        candidates = result_data.get("candidates", [])
        # The model expects a list of dicts, so this is correct
        self.model = DictListModel(candidates)
        self.table_view.setModel(self.model)
        self.table_view.resizeColumnsToContents()
        self.layout.addWidget(self.table_view)


class GrainFinderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find Data Grain Options")
        self.layout = QFormLayout(self)

        self.normalize_ws_check = QCheckBox("Normalize Whitespace")
        self.normalize_ws_check.setChecked(True)
        self.layout.addRow("Normalization:", self.normalize_ws_check)

        self.lowercase_check = QCheckBox("Lowercase Strings")
        self.lowercase_check.setChecked(False)
        self.layout.addRow("", self.lowercase_check)

        self.ok_button = QPushButton("Find Grain")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def get_options(self):
        return {
            "normalize_whitespace": self.normalize_ws_check.isChecked(),
            "lowercase_strings": self.lowercase_check.isChecked()
        }


class DictListModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = list(self._data[0].keys()) if self._data else []

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and role == Qt.ItemDataRole.DisplayRole:
            row_data = self._data[index.row()]
            key = self._headers[index.column()]
            return str(row_data.get(key, ""))
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None


class HierarchyReportDialog(QDialog):
    def __init__(self, analysis_result: dict, parent=None):
        super().__init__(parent)
        self.analysis_result = analysis_result
        self.setWindowTitle("Hierarchy Report")
        self.setGeometry(150, 150, 700, 500)

        self.layout = QVBoxLayout(self)

        text_report = hierarchy_finder.format_text_report(self.analysis_result)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setText(text_report)
        self.text_edit.setFontFamily("Courier")
        self.layout.addWidget(self.text_edit)

        self.button_layout = QHBoxLayout()
        self.export_button = QPushButton("Export to File...")
        self.export_button.clicked.connect(self.show_export_dialog)
        self.copy_button = QPushButton("Copy to Clipboard...")
        self.copy_button.clicked.connect(self.show_copy_dialog)
        self.button_layout.addWidget(self.export_button)
        self.button_layout.addWidget(self.copy_button)
        self.layout.addLayout(self.button_layout)

    def show_copy_dialog(self):
        formats = {
            "Text Report": (hierarchy_finder.format_text_report, ".txt"),
            "Graphviz (.dot)": (hierarchy_finder.format_graphviz_dot, ".dot"),
            "Mermaid.js (.md)": (hierarchy_finder.format_mermaid_js, ".md")
        }
        chosen_format, ok = QInputDialog.getItem(self, "Select Format to Copy",
                                                 "Format:", formats.keys(), 0, False)
        if not ok:
            return

        formatter, _ = formats[chosen_format]
        report_content = formatter(self.analysis_result)

        clipboard = QApplication.clipboard()
        clipboard.setText(report_content)
        # Maybe add a status tip here later

    def show_export_dialog(self):
        formats = {
            "Graphviz (.dot)": (hierarchy_finder.format_graphviz_dot, ".dot"),
            "Mermaid.js (.md)": (hierarchy_finder.format_mermaid_js, ".md"),
            "Text Report (.txt)": (hierarchy_finder.format_text_report, ".txt")
        }
        chosen_format, ok = QInputDialog.getItem(self, "Select Export Format",
                                                 "Format:", formats.keys(), 0, False)
        if not ok:
            return

        formatter, extension = formats[chosen_format]
        report_content = formatter(self.analysis_result)

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", f"hierarchy_report{extension}", f"Report Files (*{extension})")
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText(f"Error saving file: {e}")
            msg_box.setWindowTitle("Save Error")
            msg_box.exec()


class HierarchyOptionsDialog(QDialog):
    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find Hierarchies Options")
        self.layout = QFormLayout(self)

        self.parent_combo = QComboBox()
        self.parent_combo.addItems(columns)
        self.layout.addRow("Parent Column:", self.parent_combo)

        self.child_combo = QComboBox()
        self.child_combo.addItems(columns)
        # Select second item by default if available
        if len(columns) > 1:
            self.child_combo.setCurrentIndex(1)
        self.layout.addRow("Child Column:", self.child_combo)

        self.swap_button = QPushButton("Swap")
        self.swap_button.clicked.connect(self.swap_columns)
        self.layout.addWidget(self.swap_button)

        self.ok_button = QPushButton("Find Hierarchies")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def swap_columns(self):
        parent_index = self.parent_combo.currentIndex()
        child_index = self.child_combo.currentIndex()
        self.parent_combo.setCurrentIndex(child_index)
        self.child_combo.setCurrentIndex(parent_index)

    def get_options(self):
        return {
            "parent_col": self.parent_combo.currentText(),
            "child_col": self.child_combo.currentText()
        }


class GrainReportDialog(QDialog):
    def __init__(self, result_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Grain Analysis Report")
        self.setGeometry(150, 150, 800, 600)

        self.layout = QVBoxLayout(self)

        # Summary Info
        total_rows = result_data.get("total_rows", "N/A")
        candidate_grains = result_data.get("candidate_grains", [])
        grains_str = "\n".join([", ".join(g) for g in candidate_grains]) or "None found"

        summary_text = (
            f"<b>Total Rows:</b> {total_rows}<br>"
            f"<b>Candidate Grain(s):</b><br>{grains_str}"
        )
        self.summary_label = QLabel(summary_text)
        self.summary_label.setTextFormat(Qt.TextFormat.RichText)
        self.layout.addWidget(self.summary_label)

        # Uniqueness Table
        self.table_view = QTableView()
        summary_data = result_data.get("uniqueness_summary", [])
        self.model = DictListModel(summary_data)
        self.table_view.setModel(self.model)
        self.table_view.resizeColumnsToContents()
        self.layout.addWidget(self.table_view)

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.layout.addWidget(self.copy_button)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        model = self.table_view.model()
        if not model:
            return

        # Prepare header
        header = [model.headerData(i, Qt.Orientation.Horizontal) for i in range(model.columnCount())]
        clipboard_text = "\t".join(header) + "\n"

        # Prepare data rows
        for r in range(model.rowCount()):
            row_data = [model.data(model.index(r, c)) for c in range(model.columnCount())]
            clipboard_text += "\t".join(row_data) + "\n"

        clipboard.setText(clipboard_text)
        # Show feedback to the user, e.g., in a status bar if the dialog had one,
        # or a simple pop-up, or just nothing for simplicity.
        # For now, we'll just rely on the button press feedback.


class UniqueValuesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Unique Values Options")
        self.layout = QFormLayout(self)

        self.case_sensitive_check = QCheckBox("Case-sensitive")
        self.case_sensitive_check.setChecked(False)

        self.include_frequency_check = QCheckBox("Include frequency count")
        self.include_frequency_check.setChecked(True)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Alphabetical (A-Z)", "Frequency (High to Low)"])

        self.layout.addRow("Case Sensitivity:", self.case_sensitive_check)
        self.layout.addRow("Frequency Count:", self.include_frequency_check)
        self.layout.addRow("Sort Order:", self.sort_combo)

        self.ok_button = QPushButton("Export")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def get_options(self):
        return {
            "case_sensitive": self.case_sensitive_check.isChecked(),
            "include_frequency": self.include_frequency_check.isChecked(),
            "sort_by": self.sort_combo.currentText()
        }


class Worker(QObject):
    """
    A worker object that runs a task in a separate thread.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """
        Execute the task.
        """
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception:
            self.error.emit(traceback.format_exc())


class ReportOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Report")
        self.layout = QFormLayout(self)

        self.profiler_combo = QComboBox()
        self.profiler_combo.addItems([
            "Data Modeling Report",
            "csvkit (raw stats)",
            "YData-Profiling",
            "Sweetviz",
            "Dataprep.EDA"
        ])
        self.layout.addRow("Select Profiler:", self.profiler_combo)

        self.open_after_save_check = QCheckBox("Open file after saving")
        self.open_after_save_check.setChecked(True)
        self.layout.addRow(self.open_after_save_check)

        self.ok_button = QPushButton("Generate")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addRow(self.ok_button)

    def get_options(self):
        return {
            "profiler": self.profiler_combo.currentText(),
            "open_after_save": self.open_after_save_check.isChecked()
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Profiler")
        self.setGeometry(100, 100, 900, 700)

        # Main layout container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout(main_widget)

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter data in current tab...")
        self.filter_input.textChanged.connect(self.filter_data)
        self.layout.addWidget(self.filter_input)

        # Tab widget for multiple files
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.layout.addWidget(self.tab_widget)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        data_menu = menu_bar.addMenu("&Data")
        tools_menu = menu_bar.addMenu("&Tools")

        analysis_menu = data_menu.addMenu("Analyze")

        detect_keys_action = QAction("Detect Keys...", self)
        detect_keys_action.setStatusTip("Scan the current file to find primary key candidates")
        detect_keys_action.triggered.connect(self.show_key_detector_dialog)
        analysis_menu.addAction(detect_keys_action)

        open_action = QAction("Open", self)
        open_action.setStatusTip("Open a CSV file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self.report_action = QAction("Generate Report", self)
        self.report_action.setStatusTip("Generate a report from the data")
        self.report_action.triggered.connect(self.show_report_dialog)
        tools_menu.addAction(self.report_action)

        export_unique_action = QAction("Export Unique Values", self)
        export_unique_action.setStatusTip("Export unique values for each column to text files")
        export_unique_action.triggered.connect(self.show_export_unique_dialog)
        tools_menu.addAction(export_unique_action)

        grain_finder_action = QAction("Find Data Grain", self)
        grain_finder_action.setStatusTip("Analyze column combinations to find potential composite keys")
        grain_finder_action.triggered.connect(self.show_grain_finder_dialog)
        tools_menu.addAction(grain_finder_action)

        hierarchy_finder_action = QAction("Find Hierarchies", self)
        hierarchy_finder_action.setStatusTip("Detect one-to-many relationships between columns")
        hierarchy_finder_action.triggered.connect(self.show_hierarchy_finder_dialog)
        tools_menu.addAction(hierarchy_finder_action)

        tools_menu.addSeparator()

        generate_queries_action = QAction("Generate SQL Queries...", self)
        generate_queries_action.setStatusTip("Generate a standard set of SQL profiling queries")
        generate_queries_action.triggered.connect(self.show_query_generator_dialog)
        tools_menu.addAction(generate_queries_action)

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(detect_keys_action)
        toolbar.addSeparator()
        toolbar.addAction(self.report_action)
        toolbar.addAction(export_unique_action)
        toolbar.addAction(grain_finder_action)
        toolbar.addAction(hierarchy_finder_action)
        toolbar.addAction(generate_queries_action)

        # Status Bar
        self.setStatusBar(QStatusBar(self))

        self.tabs_data = [] # To store data for each tab

        self.thread = None
        self.worker = None

    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        if index < len(self.tabs_data):
            del self.tabs_data[index]

    def show_error_message(self, text):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(text)
        msg_box.setWindowTitle("Error")
        msg_box.exec()

    def open_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open CSV(s)", "", "CSV Files (*.csv);;All Files (*)")
        if not file_paths:
            return

        for file_path in file_paths:
            try:
                df = pd.read_csv(file_path, delimiter=",", encoding='utf-8')

                # Create a new tab
                table_view = QTableView()
                proxy_model = QSortFilterProxyModel()
                pandas_model = PandasModel(df)
                proxy_model.setSourceModel(pandas_model)
                proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                proxy_model.setFilterKeyColumn(-1)
                table_view.setModel(proxy_model)

                # Store data for this tab
                tab_data = {
                    'df': df,
                    'proxy_model': proxy_model,
                    'file_path': file_path
                }
                self.tabs_data.append(tab_data)

                tab_name = os.path.basename(file_path)
                index = self.tab_widget.addTab(table_view, tab_name)
                self.tab_widget.setCurrentIndex(index)

            except Exception as e:
                self.show_error_message(f"Error loading file {file_path}:\n{e}")
                continue # Continue to next file

    def filter_data(self, text):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0 or current_index >= len(self.tabs_data):
            return

        proxy_model = self.tabs_data[current_index]['proxy_model']
        proxy_model.setFilterRegularExpression(text)

    def show_report_dialog(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            self.show_error_message("Please open a file first.")
            return

        if self.thread is not None and self.thread.isRunning():
            self.show_error_message("A report is already being generated.")
            return

        dialog = ReportOptionsDialog(self)
        if not dialog.exec():
            return

        self.options = dialog.get_options()

        self.thread = QThread()
        self.worker = Worker(self._generate_report_task)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_report_finished)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.report_action.setEnabled(False)
        self.statusBar().showMessage(f"Generating report with {self.options['profiler']}... (this may take a while)")

    def _generate_report_task(self):
        profiler_name = self.options['profiler']
        current_tab_data = self.tabs_data[self.tab_widget.currentIndex()]
        df = current_tab_data['df']
        file_path = current_tab_data['file_path']

        if profiler_name == "Data Modeling Report":
            command = ["csvstat", "--delimiter", ",", "--json", file_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            report_content = generate_recommendations(result.stdout, file_path)
            return report_content, ".txt"
        elif profiler_name == "csvkit (raw stats)":
            # Returns a dictionary of reports
            return profilers.run_csvkit(file_path, ","), None
        elif profiler_name == "YData-Profiling":
            return profilers.run_ydata_profiling(df), ".html"
        elif profiler_name == "Sweetviz":
            return profilers.run_sweetviz(df), ".html"
        elif profiler_name == "Dataprep.EDA":
            return profilers.run_dataprep(df), ".html"

        raise NotImplementedError(f"Profiler '{profiler_name}' is not implemented yet.")

    def _on_report_finished(self, result):
        self.statusBar().clearMessage()
        self.report_action.setEnabled(True)

        report_content, file_ext = result
        self.save_report(report_content, file_ext, self.options['open_after_save'])
        self.thread = None # Fix RuntimeError by nullifying the thread

    def save_report(self, content, extension, open_after_save):
        if isinstance(content, dict):
            # Handle multi-file save for csvkit
            self.save_multifile_report(content, open_after_save)
            return

        # Handle single file save
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", f"report{extension}", f"Report Files (*{extension})")
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.statusBar().showMessage(f"Report saved to {file_path}", 5000)
            if open_after_save:
                webbrowser.open(f"file://{file_path}")
        except Exception as e:
            self.show_error_message(f"Error saving file: {e}")

    def save_multifile_report(self, reports: dict, open_after_save):
        # Ask for a base filename, e.g., "my_report"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Reports", "report", "All Files (*)")
        if not file_path:
            return

        # Strip extension if user provides one
        base_path, _ = os.path.splitext(file_path)

        try:
            saved_paths = []
            for ext, content in reports.items():
                path = f"{base_path}.{ext}"
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                saved_paths.append(path)

            self.statusBar().showMessage(f"Reports saved: {', '.join(p for p in saved_paths)}", 8000)

            if open_after_save and saved_paths:
                # Open the first created file
                webbrowser.open(f"file://{saved_paths[0]}")

        except Exception as e:
            self.show_error_message(f"Error saving files: {e}")


    def show_export_unique_dialog(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            self.show_error_message("Please open a file first.")
            return

        if self.thread is not None and self.thread.isRunning():
            self.show_error_message("Another process is already running.")
            return

        dialog = UniqueValuesDialog(self)
        if not dialog.exec():
            return

        options = dialog.get_options()

        # Ask for output directory
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not dir_path:
            return

        self.thread = QThread()
        self.worker = Worker(self._export_unique_values_task, options, dir_path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_export_finished)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        self.thread.start()
        self.statusBar().showMessage("Exporting unique values...")

    def _export_unique_values_task(self, options, dir_path):
        current_tab_data = self.tabs_data[self.tab_widget.currentIndex()]
        df = current_tab_data['df']
        file_path = current_tab_data['file_path']

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = os.path.join(dir_path, base_name)

        return exporter.export_unique_values(df, output_dir, options)

    def _on_export_finished(self, message):
        self.statusBar().showMessage(message, 8000)

    def show_grain_finder_dialog(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            self.show_error_message("Please open a file first.")
            return

        if self.thread is not None and self.thread.isRunning():
            self.show_error_message("Another process is already running.")
            return

        dialog = GrainFinderDialog(self)
        if not dialog.exec():
            return

        options = dialog.get_options()

        self.thread = QThread()
        self.worker = Worker(self._run_grain_finder_task, options)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_grain_finder_finished)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        self.thread.start()
        self.statusBar().showMessage("Finding data grain... this may take a while.")

    def _run_grain_finder_task(self, options):
        current_tab_data = self.tabs_data[self.tab_widget.currentIndex()]
        file_path = current_tab_data['file_path']

        return grain_finder.infer_grain_from_csv(
            csv_path=file_path,
            normalize_whitespace=options['normalize_whitespace'],
            lowercase_strings=options['lowercase_strings']
        )

    def _on_grain_finder_finished(self, result_data):
        self.statusBar().clearMessage()
        dialog = GrainReportDialog(result_data, self)
        dialog.exec()

    def show_key_detector_dialog(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            self.show_error_message("Please open a file first.")
            return

        if self.thread is not None and self.thread.isRunning():
            self.show_error_message("Another process is already running.")
            return

        dialog = KeyDetectorOptionsDialog(self)
        if not dialog.exec():
            return

        options = dialog.get_options()

        self.thread = QThread()
        self.worker = Worker(self._run_key_detector_task, options)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_key_detector_finished)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        self.thread.start()
        self.statusBar().showMessage("Detecting primary key candidates... this may take a while.")

    def _run_key_detector_task(self, options):
        current_tab_data = self.tabs_data[self.tab_widget.currentIndex()]
        file_path = current_tab_data['file_path']

        # In later phases, options will be passed in
        return key_detector.detect_single_column_keys(
            csv_path=file_path
        )

    def _on_key_detector_finished(self, result_data):
        self.statusBar().clearMessage()
        dialog = KeyDetectorReportDialog(result_data, self)
        dialog.exec()

    def show_hierarchy_finder_dialog(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            self.show_error_message("Please open a file first.")
            return

        if self.thread is not None and self.thread.isRunning():
            self.show_error_message("Another process is already running.")
            return

        current_tab_data = self.tabs_data[current_index]
        columns = list(current_tab_data['df'].columns)
        if len(columns) < 2:
            self.show_error_message("You need at least two columns to find a hierarchy.")
            return

        dialog = HierarchyOptionsDialog(columns, self)
        if not dialog.exec():
            return

        options = dialog.get_options()
        if options['parent_col'] == options['child_col']:
            self.show_error_message("Parent and Child columns cannot be the same.")
            return

        self.thread = QThread()
        self.worker = Worker(self._run_hierarchy_finder_task, options)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_hierarchy_finder_finished)
        self.worker.error.connect(self.show_error_message)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'thread', None))

        self.thread.start()
        self.statusBar().showMessage("Finding hierarchies... this may take a while.")

    def _run_hierarchy_finder_task(self, options):
        current_tab_data = self.tabs_data[self.tab_widget.currentIndex()]
        df = current_tab_data['df']
        return hierarchy_finder.build_hierarchies_from_columns(
            df,
            parent_col=options['parent_col'],
            child_col=options['child_col']
        )

    def _on_hierarchy_finder_finished(self, analysis_result):
        self.statusBar().clearMessage()
        dialog = HierarchyReportDialog(analysis_result, self)
        dialog.exec()

    def show_query_generator_dialog(self):
        current_index = self.tab_widget.currentIndex()
        default_table_name = "your_table_name"

        if current_index >= 0:
            file_path = self.tabs_data[current_index]['file_path']
            default_table_name = os.path.splitext(os.path.basename(file_path))[0]

        table_name, ok = QInputDialog.getText(self, "Enter Table Name",
                                              "Please enter the name of the table:",
                                              QLineEdit.EchoMode.Normal,
                                              default_table_name)

        if not ok or not table_name.strip():
            return  # User cancelled or entered an empty/whitespace name

        try:
            # Call the simplified query generator
            query_string = query_generator.generate_queries(table_name.strip())
            report_dialog = QueryReportDialog(query_string, self)
            report_dialog.exec()
        except Exception as e:
            self.show_error_message(f"Error generating queries: {e}\n{traceback.format_exc()}")

    def closeEvent(self, event):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
