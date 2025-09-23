import sys
import pandas as pd
import webbrowser
import tempfile
import subprocess
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStatusBar, QToolBar,
                             QTableView, QFileDialog, QLineEdit, QVBoxLayout,
                             QWidget, QDialog, QTextEdit, QMessageBox,
                             QComboBox, QPushButton, QFormLayout, QCheckBox)
from PyQt6.QtGui import QAction
from table_model import PandasModel
from reporter import generate_recommendations
import profilers


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
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter...")
        self.filter_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.filter_input)

        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        tools_menu = menu_bar.addMenu("&Tools")

        open_action = QAction("Open", self)
        open_action.setStatusTip("Open a CSV file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        exit_action = QAction("Exit", self)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        report_action = QAction("Generate Report", self)
        report_action.setStatusTip("Generate a report from the data")
        report_action.triggered.connect(self.show_report_dialog)
        tools_menu.addAction(report_action)

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(report_action)

        # Status Bar
        self.setStatusBar(QStatusBar(self))

        self.df = None
        self.proxy_model = None
        self.file_path = None
        self.delimiter = None

    def show_error_message(self, text):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(text)
        msg_box.setWindowTitle("Error")
        msg_box.exec()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                self.file_path = file_path
                self.delimiter = ","
                self.df = pd.read_csv(self.file_path, delimiter=self.delimiter, encoding='utf-8')
                model = PandasModel(self.df)

                self.proxy_model = QSortFilterProxyModel()
                self.proxy_model.setSourceModel(model)
                self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.proxy_model.setFilterKeyColumn(-1)  # Filter on all columns

                self.table_view.setModel(self.proxy_model)
                self.statusBar().showMessage(f"Loaded {self.file_path}", 5000)
            except Exception as e:
                self.show_error_message(f"Error loading file: {e}")

    def filter_data(self, text):
        if self.proxy_model:
            self.proxy_model.setFilterRegularExpression(text)

    def show_report_dialog(self):
        if self.df is None:
            self.show_error_message("Please open a file first.")
            return

        dialog = ReportOptionsDialog(self)
        if not dialog.exec():
            return

        options = dialog.get_options()
        profiler_name = options['profiler']
        self.statusBar().showMessage(f"Generating report using {profiler_name}...", 10000)

        try:
            report_content = ""
            file_ext = ".html"
            if profiler_name == "Data Modeling Report":
                command = ["csvstat", "--delimiter", self.delimiter, "--json", self.file_path]
                result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
                report_content = generate_recommendations(result.stdout, self.file_path)
                self.save_report_file(report_content, ".txt", options['open_after_save'])
            elif profiler_name == "csvkit (raw stats)":
                self.run_csvkit_profiler(options['open_after_save'])
            elif profiler_name == "YData-Profiling":
                report_content = profilers.run_ydata_profiling(self.df)
                self.save_report_file(report_content, ".html", options['open_after_save'])
            elif profiler_name == "Sweetviz":
                report_content = profilers.run_sweetviz(self.df)
                self.save_report_file(report_content, ".html", options['open_after_save'])
            elif profiler_name == "Dataprep.EDA":
                report_content = profilers.run_dataprep(self.df)
                self.save_report_file(report_content, ".html", options['open_after_save'])

        except Exception as e:
            self.show_error_message(f"Failed to generate report with {profiler_name}:\n{e}")
        finally:
            self.statusBar().clearMessage()

    def run_csvkit_profiler(self, open_after_save):
        formats = ("txt", "json", "csv")
        output_format, ok = QInputDialog.getItem(self, "CSVKit Output Format",
                                                 "Select output format:", formats, 0, False)
        if not ok:
            return

        command = ["csvstat", "--delimiter", self.delimiter, self.file_path]
        if output_format == "json":
            command.insert(1, "--json")
        elif output_format == "csv":
            command.insert(1, "--csv")

        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        report_content = result.stdout
        self.save_report_file(report_content, f".{output_format}", open_after_save)

    def save_report_file(self, content, extension, open_after_save):
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


    def closeEvent(self, event):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
