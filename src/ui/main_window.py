import sys
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Converter")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create dummy widgets for tabs for now
        from .sqlite_converter_widget import SQLiteConverterWidget
        from .excel_converter_widget import ExcelConverterWidget
        from .pdf_operations_widget import PdfOperationsWidget
        self.sqlite_tab = SQLiteConverterWidget()
        self.excel_tab = ExcelConverterWidget()
        self.pdf_operations_tab = PdfOperationsWidget()

        self.tabs.addTab(self.sqlite_tab, "SQLite to CSV/TSV")
        self.tabs.addTab(self.excel_tab, "Excel to CSV/TSV")
        self.tabs.addTab(self.pdf_operations_tab, "PDF Operations")