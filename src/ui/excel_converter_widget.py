from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QRadioButton, QGroupBox, QHBoxLayout, QProgressBar, QTextEdit, QListWidget, QAbstractItemView
from PyQt6.QtCore import QThread
from src.converters.excel_converter import ExcelConverter

class ExcelConverterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = []
        self.output_dir = ""
        self.worker_thread = None

        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)

        # File selection
        file_button_layout = QHBoxLayout()
        self.select_files_button = QPushButton("Select Excel Files")
        self.select_files_button.clicked.connect(self.select_files)
        file_button_layout.addWidget(self.select_files_button)

        self.remove_files_button = QPushButton("Remove Selected")
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        file_button_layout.addWidget(self.remove_files_button)
        self.layout.addLayout(file_button_layout)

        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.layout.addWidget(self.file_list)

        # Output directory selection
        self.select_output_dir_button = QPushButton("Select Output Directory")
        self.select_output_dir_button.clicked.connect(self.select_output_dir)
        self.output_dir_label = QLabel("No directory selected.")
        self.layout.addWidget(self.select_output_dir_button)
        self.layout.addWidget(self.output_dir_label)

        # Delimiter options
        delimiter_group = QGroupBox("Delimiter")
        delimiter_layout = QHBoxLayout()
        self.comma_radio = QRadioButton(",")
        self.tab_radio = QRadioButton("Tab")
        self.semicolon_radio = QRadioButton(";")
        self.comma_radio.setChecked(True)
        delimiter_layout.addWidget(self.comma_radio)
        delimiter_layout.addWidget(self.tab_radio)
        delimiter_layout.addWidget(self.semicolon_radio)
        delimiter_group.setLayout(delimiter_layout)
        self.layout.addWidget(delimiter_group)

        # Convert button
        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.start_conversion)
        self.layout.addWidget(self.convert_button)

        # Progress and logging
        self.progress_bar = QProgressBar()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.log_area)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Excel Files", "", "Excel Files (*.xlsx *.xls)")
        if files:
            self.add_files(files)

    def select_output_dir(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir:
            self.output_dir = dir
            self.output_dir_label.setText(dir)

    def get_delimiter(self):
        if self.tab_radio.isChecked():
            return '\t'
        if self.semicolon_radio.isChecked():
            return ';'
        return ','

    def start_conversion(self):
        if self.file_list.count() == 0:
            self.log_message("Please select files to convert.")
            return
        if not self.output_dir:
            self.log_message("Please select an output directory.")
            return

        self.convert_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_area.clear()

        files_to_convert = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        delimiter = self.get_delimiter()
        self.worker = ExcelConverter(files_to_convert, self.output_dir, delimiter)
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

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.xlsx', '.xls')):
                files.append(file_path)

        if files:
            self.add_files(files)

    def remove_selected_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))