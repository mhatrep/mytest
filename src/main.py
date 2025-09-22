import sys
import pandas as pd
import webbrowser
import tempfile
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStatusBar, QToolBar,
                             QTableView, QFileDialog, QInputDialog, QLineEdit,
                             QVBoxLayout, QWidget)
from PyQt6.QtGui import QAction
from table_model import PandasModel


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

        open_action = QAction("Open", self)
        open_action.setStatusTip("Open a CSV file")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        profile_action = QAction("Profile Data", self)
        profile_action.setStatusTip("Generate a profile report of the data")
        profile_action.triggered.connect(self.profile_data)
        file_menu.addAction(profile_action)

        exit_action = QAction("Exit", self)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(open_action)
        toolbar.addAction(profile_action)

        # Status Bar
        self.setStatusBar(QStatusBar(self))

        self.df = None
        self.proxy_model = None

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                delimiter, ok = QInputDialog.getText(self, 'Delimiter', 'Enter delimiter:', text=',')
                if ok:
                    self.df = pd.read_csv(file_path, delimiter=delimiter)
                    model = PandasModel(self.df)

                    self.proxy_model = QSortFilterProxyModel()
                    self.proxy_model.setSourceModel(model)
                    self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                    self.proxy_model.setFilterKeyColumn(-1)  # Filter on all columns

                    self.table_view.setModel(self.proxy_model)
                    self.statusBar().showMessage(f"Loaded {file_path}", 5000)
            except Exception as e:
                self.statusBar().showMessage(f"Error loading file: {e}", 5000)

    def filter_data(self, text):
        if self.proxy_model:
            self.proxy_model.setFilterRegularExpression(text)

    def profile_data(self):
        if self.df is not None:
            self.statusBar().showMessage("Profiling data...", 5000)
            try:
                # Generate a description of the data
                description = self.df.describe(include='all').to_html()

                # Save to a temporary HTML file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
                    tmp_file.write(description.encode('utf-8'))
                    webbrowser.open(f"file://{tmp_file.name}")

                self.statusBar().showMessage("Profiling report generated and opened in browser.", 5000)
            except Exception as e:
                self.statusBar().showMessage(f"Error profiling data: {e}", 5000)
        else:
            self.statusBar().showMessage("No data loaded to profile.", 5000)

    def closeEvent(self, event):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
