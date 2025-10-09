from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QAbstractItemView, QTextEdit, QHBoxLayout
from PyQt6.QtCore import QThread
from src.converters.pdf_merger import PdfMerger

class PdfMergerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)

        # File selection
        file_button_layout = QHBoxLayout()
        self.select_files_button = QPushButton("Select PDF Files to Merge")
        self.select_files_button.clicked.connect(self.select_files)
        file_button_layout.addWidget(self.select_files_button)

        self.remove_files_button = QPushButton("Remove Selected")
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        file_button_layout.addWidget(self.remove_files_button)
        self.layout.addLayout(file_button_layout)

        # File list
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layout.addWidget(self.file_list)

        # Merge button
        self.merge_button = QPushButton("Merge PDFs")
        self.merge_button.clicked.connect(self.start_merging)
        self.layout.addWidget(self.merge_button)

        # Logging
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if files:
            self.add_files(files)

    def start_merging(self):
        if self.file_list.count() < 2:
            self.log_message("Please select at least two PDF files to merge.")
            return

        output_file, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "", "PDF Files (*.pdf)")
        if not output_file:
            return

        self.merge_button.setEnabled(False)
        self.log_area.clear()

        files_to_merge = [self.file_list.item(i).text() for i in range(self.file_list.count())]

        self.worker = PdfMerger(files_to_merge, output_file)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.merging_finished)
        self.worker.log_message.connect(self.log_message)

        self.worker_thread.start()

    def merging_finished(self):
        self.log_message("Merging finished.")
        self.merge_button.setEnabled(True)
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.worker_thread = None

    def log_message(self, message):
        self.log_area.append(message)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.pdf'):
                files.append(file_path)

        if files:
            self.add_files(files)

    def add_files(self, files):
        current_files = {self.file_list.item(i).text() for i in range(self.file_list.count())}
        for file in files:
            if file not in current_files:
                self.file_list.addItem(file)

    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))