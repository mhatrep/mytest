import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeView,
    QLineEdit,
    QCheckBox,
    QMenuBar,
    QFileDialog,
)
from src.data_loader import load_data
from src.tree_model import TreeModel
from src.filter_proxy_model import FilterProxyModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Viewer")
        self.resize(800, 600)

        # Create widgets
        self.tree_view = QTreeView()
        self.tree_view.header().setStretchLastSection(True)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter values...")
        self.case_sensitive_checkbox = QCheckBox("Case Sensitive")

        # Layout
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(self.case_sensitive_checkbox)

        main_layout = QVBoxLayout()
        main_layout.addLayout(filter_layout)
        main_layout.addWidget(self.tree_view)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create menu bar
        self._create_menu_bar()

        # Connect signals
        self.filter_input.textChanged.connect(self._on_filter_text_changed)
        self.case_sensitive_checkbox.toggled.connect(self._on_case_sensitive_toggled)

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        open_action = file_menu.addAction("&Open")
        open_action.triggered.connect(self._open_file)

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*);;JSON Files (*.json);;YAML Files (*.yaml *.yml);;XML Files (*.xml)"
        )
        if file_path:
            try:
                data = load_data(file_path)
                self.model = TreeModel(data)
                self.proxy_model = FilterProxyModel()
                self.proxy_model.setSourceModel(self.model)
                self.tree_view.setModel(self.proxy_model)
                self.tree_view.expandAll()
            except Exception as e:
                print(f"Error loading file: {e}")

    def _on_filter_text_changed(self, text):
        if hasattr(self, "proxy_model"):
            self.proxy_model.set_filter_text(text)
            self.tree_view.expandAll()


    def _on_case_sensitive_toggled(self, checked):
        if hasattr(self, "proxy_model"):
            self.proxy_model.set_case_sensitive(checked)
            self.tree_view.expandAll()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())