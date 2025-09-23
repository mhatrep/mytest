import sys
import pandas as pd
import webbrowser
import tempfile
import subprocess
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStatusBar, QToolBar,
                             QTableView, QFileDialog, QInputDialog, QLineEdit,
                             QVBoxLayout, QWidget, QDialog, QTextEdit)
from PyQt6.QtGui import QAction
from table_model import PandasModel
from reporter import generate_recommendations


class ReportDialog(QDialog):
    def __init__(self, report_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Modeling Report")
        self.setGeometry(150, 150, 700, 500)
        layout = QVBoxLayout(self)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(report_text)
        text_edit.setFontFamily("Courier")
        layout.addWidget(text_edit)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Profiler")
        self.setGeometry(100, 100, 800, 600)

        # Main layout and central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter...")
        self.filter_input.textChanged.connect(self.filter_data)
        layout.addWidget(self.filter_input)

        # Table View
        self.table_view = QTableView()
        layout.addWidget(self.table_view)

        # Menu Bar
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

        profile_action = QAction("Profile Data (csvstat)", self)
        profile_action.setStatusTip("Generate a basic profile report using csvstat")
        profile_action.triggered.connect(self.profile_data)
        tools_menu.addAction(profile_action)

        recommend_action = QAction("Generate Modeling Report", self)
        recommend_action.setStatusTip("Generate a data modeling recommendation report")
        recommend_action.triggered.connect(self.generate_modeling_report)
        tools_menu.addAction(recommend_action)


        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(profile_action)
        toolbar.addAction(recommend_action)

        # Status Bar
        self.setStatusBar(QStatusBar(self))

        self.df = None
        self.proxy_model = None
        self.file_path = None
        self.delimiter = None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                self.file_path = file_path
                self.delimiter = ","
                self.df = pd.read_csv(self.file_path, delimiter=self.delimiter)
                model = PandasModel(self.df)

                self.proxy_model = QSortFilterProxyModel()
                self.proxy_model.setSourceModel(model)
                self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.proxy_model.setFilterKeyColumn(-1)  # Filter on all columns

                self.table_view.setModel(self.proxy_model)
                self.statusBar().showMessage(f"Loaded {self.file_path}", 5000)
            except Exception as e:
                self.statusBar().showMessage(f"Error loading file: {e}", 5000)

    def filter_data(self, text):
        if self.proxy_model:
            self.proxy_model.setFilterRegularExpression(text)

    def profile_data(self):
        if self.file_path is None:
            self.statusBar().showMessage("No data loaded to profile.", 5000)
            return

        formats = ("txt", "json", "csv")
        output_format, ok = QInputDialog.getItem(self, "Output Format",
                                                 "Select output format:", formats, 0, False)
        if not ok:
            return

        self.statusBar().showMessage(f"Generating {output_format} report...", 5000)
        try:
            command = ["csvstat", "--delimiter", self.delimiter, self.file_path]
            if output_format == "json":
                command.insert(1, "--json")
            elif output_format == "csv":
                command.insert(1, "--csv")

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            report_content = result.stdout

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}", mode="w") as tmp_file:
                tmp_file.write(report_content)
                webbrowser.open(f"file://{tmp_file.name}")

            self.statusBar().showMessage("Profiling report generated and opened.", 5000)
        except FileNotFoundError:
            self.statusBar().showMessage("Error: csvkit not found. Please ensure it is installed and in your PATH.", 10000)
        except subprocess.CalledProcessError as e:
            self.statusBar().showMessage(f"Error running csvstat: {e.stderr}", 10000)
        except Exception as e:
            self.statusBar().showMessage(f"An unexpected error occurred: {e}", 10000)

    def generate_modeling_report(self):
        if self.file_path is None:
            self.statusBar().showMessage("No data loaded to generate a report.", 5000)
            return

        self.statusBar().showMessage("Generating modeling report...", 10000)
        try:
            # Get stats as JSON
            command = ["csvstat", "--delimiter", self.delimiter, "--json", self.file_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            stats_json = result.stdout

            # Generate recommendations
            report_text = generate_recommendations(stats_json, self.file_path)

            # Display in dialog
            dialog = ReportDialog(report_text, self)
            dialog.exec()
            self.statusBar().showMessage("Modeling report generated successfully.", 5000)

        except FileNotFoundError:
            self.statusBar().showMessage("Error: csvkit not found. Please ensure it is installed and in your PATH.", 10000)
        except subprocess.CalledProcessError as e:
            self.statusBar().showMessage(f"Error running csvstat: {e.stderr}", 10000)
        except Exception as e:
            self.statusBar().showMessage(f"An unexpected error occurred: {e}", 10000)

    def closeEvent(self, event):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
