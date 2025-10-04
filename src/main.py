import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
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
    QStatusBar,
    QDockWidget,
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, QObject, QThread, pyqtSignal

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]

class Worker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(list)

    def __init__(self, dir_path):
        super().__init__()
        self.dir_path = dir_path

    def run(self):
        image_paths = []
        for root, _, files in os.walk(self.dir_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in SUPPORTED_FORMATS):
                    image_paths.append(os.path.join(root, file))
        self.result.emit(image_paths)
        self.finished.emit()

class ImageSearchApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Search")
        self.image_paths = []
        self.init_ui()
        self.apply_stylesheet()
        self.show()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QDockWidget {
                titlebar-close-icon: none;
                titlebar-float-icon: none;
            }
            QDockWidget::title {
                background-color: #3c3f41;
                color: #f0f0f0;
                padding: 5px;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #f0f0f0;
                border: none;
            }
            QPushButton {
                background-color: #3c3f41;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4e5254;
            }
            QLineEdit {
                background-color: #3c3f41;
                padding: 5px;
                border-radius: 3px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QListWidget {
                background-color: #3c3f41;
            }
            QStatusBar {
                background-color: #3c3f41;
            }
        """)

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Search dock
        search_dock = QDockWidget("Search", self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, search_dock)
        search_widget = QWidget()
        search_dock.setWidget(search_widget)
        search_layout = QVBoxLayout(search_widget)

        self.dir_button = QPushButton("Select Directory")
        self.dir_button.clicked.connect(self.select_directory)
        search_layout.addWidget(self.dir_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query")
        search_layout.addWidget(self.search_input)

        self.case_sensitive_checkbox = QCheckBox("Case Sensitive")
        search_layout.addWidget(self.case_sensitive_checkbox)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_images)
        search_layout.addWidget(self.search_button)

        search_layout.addStretch()

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

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.thread = QThread()
            self.worker = Worker(dir_path)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.result.connect(self.handle_indexing_result)
            self.thread.start()
            self.dir_button.setEnabled(False)
            self.search_button.setEnabled(False)
            self.status_bar.showMessage("Indexing images...")

    def handle_indexing_result(self, image_paths):
        self.image_paths = image_paths
        print(f"Indexed {len(self.image_paths)} images.")
        self.search_images()
        self.dir_button.setEnabled(True)
        self.search_button.setEnabled(True)
        self.status_bar.clearMessage()

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