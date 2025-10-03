import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QFileDialog,
    QCheckBox,
    QListWidgetItem,
    QLabel,
    QSplitter,
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]

class ImageSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Search")
        self.image_paths = []
        self.init_ui()
        self.show()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_button = QPushButton("Select Directory")
        self.dir_button.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.dir_button)
        main_layout.addLayout(dir_layout)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query")
        self.case_sensitive_checkbox = QCheckBox("Case Sensitive")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_images)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.case_sensitive_checkbox)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Results view and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.results_list = QListWidget()
        self.results_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.results_list.setIconSize(QSize(128, 128))
        self.results_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.results_list.itemSelectionChanged.connect(self.update_preview)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        splitter.addWidget(self.results_list)
        splitter.addWidget(self.preview_label)
        splitter.setSizes([400, 400])

        main_layout.addWidget(splitter)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.index_images(dir_path)

    def index_images(self, dir_path):
        self.image_paths = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                    self.image_paths.append(os.path.join(root, file))
        print(f"Indexed {len(self.image_paths)} images.")
        self.search_images()

    def search_images(self):
        query = self.search_input.text()
        case_sensitive = self.case_sensitive_checkbox.isChecked()
        self.results_list.clear()

        if not case_sensitive:
            query = query.lower()

        for path in self.image_paths:
            filename = os.path.basename(path)
            if not case_sensitive:
                filename = filename.lower()

            if query in filename:
                item = QListWidgetItem(QIcon(path), os.path.basename(path))
                item.setData(Qt.ItemDataRole.UserRole, path)
                self.results_list.addItem(item)

    def update_preview(self):
        selected_items = self.results_list.selectedItems()
        if selected_items:
            path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            pixmap = QPixmap(path)
            self.preview_label.setPixmap(
                pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.preview_label.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageSearchApp()
    sys.exit(app.exec())