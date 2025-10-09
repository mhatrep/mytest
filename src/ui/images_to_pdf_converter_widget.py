from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QAbstractItemView, QComboBox, QLabel, QHBoxLayout, QTextEdit, QProgressBar
from PyQt6.QtCore import QThread
from src.converters.images_to_pdf_converter import ImagesToPdfConverter

class ImagesToPdfConverterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.layout = QVBoxLayout(self)

        # File selection
        file_button_layout = QHBoxLayout()
        self.select_files_button = QPushButton("Select Images")
        self.select_files_button.clicked.connect(self.select_files)
        file_button_layout.addWidget(self.select_files_button)

        self.remove_files_button = QPushButton("Remove Selected")
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        file_button_layout.addWidget(self.remove_files_button)
        self.layout.addLayout(file_button_layout)

        # File list for reordering
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.layout.addWidget(self.file_list)

        # Orientation option
        orientation_layout = QHBoxLayout()
        self.orientation_label = QLabel("Orientation:")
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape"])
        orientation_layout.addWidget(self.orientation_label)
        orientation_layout.addWidget(self.orientation_combo)
        self.layout.addLayout(orientation_layout)

        # Convert button
        self.convert_button = QPushButton("Convert to PDF")
        self.convert_button.clicked.connect(self.start_conversion)
        self.layout.addWidget(self.convert_button)

        # Progress and logging
        self.progress_bar = QProgressBar()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.log_area)


    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if files:
            self.add_files(files)

    def start_conversion(self):
        if self.file_list.count() == 0:
            self.log_message("Please select images to convert.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not output_file:
            return

        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_area.clear()

        files_to_convert = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        orientation = self.orientation_combo.currentText()

        self.worker = ImagesToPdfConverter(files_to_convert, output_file, orientation)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.conversion_finished)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.log_message.connect(self.log_message)

        self.worker_thread.start()

    def conversion_finished(self):
        self.log_message("Conversion finished.")
        self.convert_button.setEnabled(True)
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker_thread = None

    def log_message(self, message):
        self.log_area.append(message)

    def add_files(self, files):
        current_files = {self.file_list.item(i).text() for i in range(self.file_list.count())}
        for file in files:
            if file not in current_files:
                self.file_list.addItem(file)

    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                files.append(file_path)

        if files:
            self.add_files(files)