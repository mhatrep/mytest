import sys
import os
import json
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
from PyQt6.QtCore import QSize, Qt, QObject, QThread, pyqtSignal, QTimer

SUPPORTED_FORMATS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]
CONFIG_FILE = "config.json"

class Worker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(list)

    def __init__(self, dir_paths):
        super().__init__()
        self.dir_paths = dir_paths

    def run(self):
        image_paths = []
        for dir_path in self.dir_paths:
            for root, _, files in os.walk(dir_path):
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
        self.search_results = []
        self.load_timer = QTimer()
        self.load_timer.timeout.connect(self.load_batch)
        self.init_ui()
        self.apply_stylesheet()
        self.load_config()
        self.showMaximized()

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QDockWidget::title {
                background-color: #e0e0e0;
                color: #333333;
                padding: 5px;
            }
            QWidget {
                background-color: #f0f0f0;
                color: #333333;
                border: none;
            }
            QPushButton {
                background-color: #e0e0e0;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #c0c0c0;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QLineEdit {
                background-color: #ffffff;
                padding: 5px;
                border-radius: 3px;
                border: 1px solid #c0c0c0;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #c0c0c0;
            }
            QStatusBar {
                background-color: #e0e0e0;
            }
        """)

    def init_ui(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Config dock
        config_dock = QDockWidget("Configuration", self)
        config_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetFloatable | QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, config_dock)
        config_widget = QWidget()
        config_dock.setWidget(config_widget)
        config_layout = QHBoxLayout(config_widget)

        # Directory management
        dir_group = QWidget()
        dir_layout = QVBoxLayout(dir_group)
        self.dir_list = QListWidget()
        dir_buttons_layout = QHBoxLayout()
        self.add_dir_button = QPushButton("Add Directory")
        self.add_dir_button.clicked.connect(self.add_directory)
        self.remove_dir_button = QPushButton("Remove Directory")
        self.remove_dir_button.clicked.connect(self.remove_directory)
        dir_buttons_layout.addWidget(self.add_dir_button)
        dir_buttons_layout.addWidget(self.remove_dir_button)
        dir_layout.addWidget(self.dir_list)
        dir_layout.addLayout(dir_buttons_layout)
        config_layout.addWidget(dir_group)

        # Search controls
        search_group = QWidget()
        search_layout = QVBoxLayout(search_group)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query")
        self.case_sensitive_checkbox = QCheckBox("Case Sensitive")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_indexing)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.case_sensitive_checkbox)
        search_layout.addWidget(self.search_button)
        search_layout.addStretch()
        config_layout.addWidget(search_group)

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

    def add_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            item = QListWidgetItem(dir_path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.dir_list.addItem(item)

    def remove_directory(self):
        for item in self.dir_list.selectedItems():
            self.dir_list.takeItem(self.dir_list.row(item))

    def start_indexing(self):
        checked_dirs = []
        for i in range(self.dir_list.count()):
            item = self.dir_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_dirs.append(item.text())

        if not checked_dirs:
            self.status_bar.showMessage("No directories selected for indexing.", 3000)
            return

        self.thread = QThread()
        self.worker = Worker(checked_dirs)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.result.connect(self.handle_indexing_result)
        self.thread.start()

        self.add_dir_button.setEnabled(False)
        self.remove_dir_button.setEnabled(False)
        self.search_button.setEnabled(False)
        self.status_bar.showMessage("Indexing images...")

    def handle_indexing_result(self, image_paths):
        self.image_paths = image_paths
        print(f"Indexed {len(self.image_paths)} images.")
        self.search_images()
        self.add_dir_button.setEnabled(True)
        self.remove_dir_button.setEnabled(True)
        self.search_button.setEnabled(True)
        self.status_bar.clearMessage()

    def search_images(self):
        query = self.search_input.text()
        case_sensitive = self.case_sensitive_checkbox.isChecked()

        self.results_list.clear()
        self.search_results = []

        if not case_sensitive:
            query = query.lower()

        for path in self.image_paths:
            filename = os.path.basename(path)
            if not case_sensitive:
                filename = filename.lower()

            if query in filename:
                self.search_results.append(path)

        if self.search_results:
            self.load_timer.start(50)  # Load every 50ms
            self.status_bar.showMessage(f"Loading {len(self.search_results)} images...")
        else:
            self.status_bar.showMessage("No images found.", 3000)

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

    def load_batch(self):
        batch_size = 20  # Load 20 items at a time
        for _ in range(batch_size):
            if not self.search_results:
                self.load_timer.stop()
                self.status_bar.showMessage(f"Loaded {self.results_list.count()} images.", 3000)
                return

            path = self.search_results.pop(0)
            item = QListWidgetItem(QIcon(path), os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.results_list.addItem(item)

        remaining = len(self.search_results)
        total = self.results_list.count() + remaining
        self.status_bar.showMessage(f"Loading... ({total - remaining}/{total})")

    def save_config(self):
        config = []
        for i in range(self.dir_list.count()):
            item = self.dir_list.item(i)
            config.append({
                "path": item.text(),
                "checked": item.checkState() == Qt.CheckState.Checked,
            })
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                for item_data in config:
                    item = QListWidgetItem(item_data["path"])
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Checked if item_data["checked"] else Qt.CheckState.Unchecked)
                    self.dir_list.addItem(item)
        except (json.JSONDecodeError, KeyError):
            print(f"Error reading or parsing {CONFIG_FILE}. A new one will be created on exit.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageSearchApp()
    sys.exit(app.exec())