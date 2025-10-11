import sys
import pandas as pd
import csv
import io
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableView, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QStatusBar, QLabel, QFileDialog, QDockWidget,
    QProgressBar, QButtonGroup, QRadioButton
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from models import PandasModel
from cleaner import clean_data

class Worker(QObject):
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)

    def __init__(self, data_iterator, options):
        super().__init__()
        self.data_iterator = data_iterator
        self.options = options
        self.is_cancelled = False

    def run(self):
        cleaned_chunks = []
        try:
            for chunk in self.data_iterator:
                if self.is_cancelled:
                    break
                cleaned_chunk = clean_data(chunk, self.options)
                cleaned_chunks.append(cleaned_chunk)
                # Since we don't know the total size, we can't emit progress
        finally:
            # Important: The iterator might be a file handle that needs closing
            if hasattr(self.data_iterator, 'close'):
                self.data_iterator.close()

        if not self.is_cancelled and cleaned_chunks:
            self.finished.emit(pd.concat(cleaned_chunks, ignore_index=True))
        else:
            self.finished.emit(pd.DataFrame()) # Emit empty frame on cancel/error

    def cancel(self):
        self.is_cancelled = True

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Cleaner")
        self.setGeometry(100, 100, 1200, 800)
        self.df = None # Full dataframe for clipboard data
        self.df_preview = None # Preview dataframe for files
        self.source_file_path = None
        self.source_is_clipboard = False
        self.detected_delimiter = None

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Top panel for file selection and options
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)
        self.file_path_edit = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.paste_toggle_button = QPushButton("Paste from Clipboard")
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems(["Auto", ",", "\t", "|", ";"])
        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["UTF-8", "UTF-16", "ASCII"])

        top_layout.addWidget(QLabel("File:"))
        top_layout.addWidget(self.file_path_edit)
        top_layout.addWidget(self.browse_button)
        top_layout.addWidget(self.paste_toggle_button)
        top_layout.addWidget(QLabel("Delimiter:"))
        top_layout.addWidget(self.delimiter_combo)
        top_layout.addWidget(QLabel("Encoding:"))
        top_layout.addWidget(self.encoding_combo)

        main_layout.addWidget(top_panel)

        # Center: Table preview
        self.table_preview = QTableView()
        main_layout.addWidget(self.table_preview, 1) # Give table view more space
        self.model = PandasModel(self.df)
        self.table_preview.setModel(self.model)

        # Bottom buttons
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)
        self.preview_button = QPushButton("Preview")
        self.apply_copy_button = QPushButton("Apply & Copy")
        self.apply_save_button = QPushButton("Apply & Save")
        self.reset_button = QPushButton("Reset")
        bottom_layout.addWidget(self.preview_button)
        bottom_layout.addWidget(self.apply_copy_button)
        bottom_layout.addWidget(self.apply_save_button)
        bottom_layout.addWidget(self.reset_button)
        main_layout.addWidget(bottom_panel)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress_bar = QProgressBar()
        self.status_bar.addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()
        self.status_bar.showMessage("Ready")

        # Connect signals
        self.browse_button.clicked.connect(self.browse_file)
        self.paste_toggle_button.clicked.connect(self.paste_from_clipboard)
        self.preview_button.clicked.connect(self.run_cleaning_in_thread)
        self.apply_copy_button.clicked.connect(self.copy_to_clipboard)
        self.apply_save_button.clicked.connect(self.save_to_file)
        self.reset_button.clicked.connect(self.reset_data)

        # Keyboard shortcuts
        self.setup_shortcuts()

        # Cleaning options dock widget
        self.create_cleaning_options_dock()

    def browse_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;TSV Files (*.tsv);;Text Files (*.txt);;All Files (*)")
        if file_name:
            self.source_file_path = file_name
            self.source_is_clipboard = False
            self.file_path_edit.setText(file_name)
            self.load_data()

    def paste_from_clipboard(self):
        clipboard_text = QApplication.clipboard().text()
        if clipboard_text:
            self.source_is_clipboard = True
            self.source_file_path = None
            self.df = pd.read_csv(io.StringIO(clipboard_text), sep=None, engine='python', on_bad_lines='skip')
            self.df_preview = self.df.head(1000)
            self.model = PandasModel(self.df_preview)
            self.table_preview.setModel(self.model)
            self.file_path_edit.setText("Pasted from clipboard")
            self.status_bar.showMessage(f"Loaded {len(self.df)} rows from clipboard.", 5000)
        else:
            self.status_bar.showMessage("Clipboard is empty.", 5000)

    def load_data(self):
        if self.source_is_clipboard or not self.source_file_path:
            return

        delimiter = self.delimiter_combo.currentText()
        encoding = self.encoding_combo.currentText()

        if delimiter == 'Auto':
            with open(self.source_file_path, 'r', encoding=encoding) as f:
                sample = f.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
                self.detected_delimiter = delimiter
                self.status_bar.showMessage(f"Detected delimiter: '{delimiter}'", 5000)
            except (csv.Error, TypeError):
                self.status_bar.showMessage("Could not detect delimiter, using ','", 5000)
                delimiter = ','
                self.detected_delimiter = delimiter

        try:
            # For preview, just load the first 1000 rows
            self.df_preview = pd.read_csv(self.source_file_path, sep=delimiter, encoding=encoding, engine='python', on_bad_lines='skip', nrows=1000)
            self.model = PandasModel(self.df_preview)
            self.table_preview.setModel(self.model)
            self.status_bar.showMessage(f"Previewing first {len(self.df_preview)} rows. Ready to process full file.", 5000)
        except Exception as e:
            self.status_bar.showMessage(f"Error loading file: {e}", 5000)

    def run_cleaning_in_thread(self):
        if not self.source_file_path and not self.source_is_clipboard:
            self.status_bar.showMessage("No data loaded to process.", 5000)
            return

        options = self.get_cleaning_options()

        data_iterator = None
        if self.source_is_clipboard and self.df is not None:
            # For clipboard data, we process the in-memory DataFrame
            data_iterator = iter([self.df])
        elif self.source_file_path:
            # For file data, create the iterator just-in-time
            delimiter = self.detected_delimiter or ','
            encoding = self.encoding_combo.currentText()
            try:
                data_iterator = pd.read_csv(
                    self.source_file_path, sep=delimiter, encoding=encoding,
                    engine='python', on_bad_lines='skip', chunksize=10000
                )
            except Exception as e:
                self.status_bar.showMessage(f"Error creating file reader: {e}", 5000)
                return

        if data_iterator is None:
            self.status_bar.showMessage("Could not create data iterator.", 5000)
            return

        self.thread = QThread()
        self.worker = Worker(data_iterator, options)
        self.worker.moveToThread(self.thread)

        self.cancel_button = QPushButton("Cancel")
        self.status_bar.addPermanentWidget(self.cancel_button)
        self.cancel_button.clicked.connect(self.cancel_cleaning)
        self.cancel_button.show()

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_cleaning_finished)

        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.start()

        self.preview_button.setEnabled(False)
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.progress_bar.show()
        self.status_bar.showMessage("Cleaning data...")

    def cancel_cleaning(self):
        if self.worker:
            self.worker.cancel()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.status_bar.showMessage("Cleaning cancelled.", 5000)
        self.progress_bar.hide()
        self.preview_button.setEnabled(True)
        self.cancel_button.hide()

    def on_progress(self, value):
        self.progress_bar.setValue(value)

    def on_cleaning_finished(self, cleaned_df):
        self.cleaned_df = cleaned_df  # Store full cleaned df
        preview_model = PandasModel(cleaned_df.head(1000))
        self.table_preview.setModel(preview_model)

        self.status_bar.showMessage("Cleaning complete.", 5000)
        self.progress_bar.hide()
        self.preview_button.setEnabled(True)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.hide()

    def reset_data(self):
        if not self.df.empty:
            self.model = PandasModel(self.df.head(1000))
            self.table_preview.setModel(self.model)
            if hasattr(self, 'cleaned_df'):
                del self.cleaned_df
            self.status_bar.showMessage("Data reset to original state.", 5000)

    def setup_shortcuts(self):
        # Ctrl+O: Open
        open_action = self.create_action("Open File", "Ctrl+O", self.browse_file)
        # Ctrl+S: Save As
        save_action = self.create_action("Save As", "Ctrl+S", self.save_to_file)
        # Ctrl+C: Copy
        copy_action = self.create_action("Copy", "Ctrl+C", self.copy_to_clipboard)
        # F5: Preview
        preview_action = self.create_action("Preview", "F5", self.run_cleaning_in_thread)
        # Ctrl+Z: Reset
        reset_action = self.create_action("Reset", "Ctrl+Z", self.reset_data)

        self.addActions([open_action, save_action, copy_action, preview_action, reset_action])

    def create_action(self, text, shortcut, slot):
        action = QAction(text, self)
        action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def copy_to_clipboard(self):
        if hasattr(self, 'cleaned_df'):
            output = io.StringIO()
            sep = self.delimiter_combo.currentText()
            if sep == 'Auto':
                sep = self.detected_delimiter if self.detected_delimiter else ','
            self.cleaned_df.to_csv(output, index=False, sep=sep, quoting=csv.QUOTE_ALL)
            QApplication.clipboard().setText(output.getvalue())
            self.status_bar.showMessage("Copied to clipboard.", 5000)
        else:
            self.status_bar.showMessage("No cleaned data to copy. Please run a preview first.", 5000)

    def save_to_file(self):
        if not hasattr(self, 'cleaned_df'):
            self.status_bar.showMessage("No cleaned data to save. Please run a preview first.", 5000)
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;TSV Files (*.tsv);;Text Files (*.txt);;All Files (*)")
        if file_name:
            try:
                sep = self.delimiter_combo.currentText()
                if sep == 'Auto':
                    sep = self.detected_delimiter if self.detected_delimiter else ','
                encoding = self.encoding_combo.currentText()
                self.cleaned_df.to_csv(file_name, index=False, sep=sep, encoding=encoding, quoting=csv.QUOTE_ALL)
                self.status_bar.showMessage(f"File saved to {file_name}", 5000)
            except Exception as e:
                self.status_bar.showMessage(f"Error saving file: {e}", 5000)


    def get_cleaning_options(self):
        options = {
            'scope_headers_only': self.scope_headers_only.isChecked(),
            'trim_whitespace': self.trim_whitespace.isChecked(),
            'whitespace_to': self.whitespace_to_combo.currentText(),
            'collapse_repeats': self.collapse_repeats.isChecked(),
            'tidy_punctuation': self.tidy_punctuation.isChecked(),
            'remove_invalid_chars': self.remove_invalid_chars.isChecked(),
            'allowed_chars': self.allowed_chars_edit.text(),
            'custom_replace_from': self.custom_replace_from.text(),
            'custom_replace_to': self.custom_replace_to.text(),
            'case_conversion': self.case_combo.currentText(),
            'transliterate': self.transliterate.isChecked(),
            'sql_safe_headers': self.sql_safe_checkbox.isChecked(),
            'deduplicate_headers': self.deduplicate_headers.isChecked()
        }
        return options


    def create_cleaning_options_dock(self):
        dock_widget = QDockWidget("Cleaning Options", self)
        dock_widget.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)

        # Target scope
        scope_box = QGroupBox("Target Scope")
        scope_layout = QVBoxLayout()
        self.scope_headers_only = QRadioButton("Headers only")
        self.scope_entire_file = QRadioButton("Entire file")
        self.scope_group = QButtonGroup(self)
        self.scope_group.addButton(self.scope_headers_only)
        self.scope_group.addButton(self.scope_entire_file)
        self.scope_entire_file.setChecked(True)
        scope_layout.addWidget(self.scope_headers_only)
        scope_layout.addWidget(self.scope_entire_file)
        scope_box.setLayout(scope_layout)
        options_layout.addWidget(scope_box)

        # Cleaning options
        cleaning_box = QGroupBox("General Cleaning")
        cleaning_layout = QFormLayout()
        self.trim_whitespace = QCheckBox("Trim leading/trailing whitespace")
        self.trim_whitespace.setChecked(True)
        self.whitespace_to_combo = QComboBox()
        self.whitespace_to_combo.addItems(["_", "-"])
        self.collapse_repeats = QCheckBox("Collapse repeated _ or -")
        self.collapse_repeats.setChecked(True)
        self.tidy_punctuation = QCheckBox("Remove leading/trailing _ or -")
        self.tidy_punctuation.setChecked(True)
        self.remove_invalid_chars = QCheckBox("Remove invalid characters")
        self.remove_invalid_chars.setChecked(True)
        self.allowed_chars_edit = QLineEdit("[A-Za-z0-9_ -]")
        self.custom_replace_from = QLineEdit()
        self.custom_replace_to = QLineEdit()
        cleaning_layout.addRow(self.trim_whitespace)
        cleaning_layout.addRow("Whitespace to:", self.whitespace_to_combo)
        cleaning_layout.addRow(self.collapse_repeats)
        cleaning_layout.addRow(self.tidy_punctuation)
        cleaning_layout.addRow(self.remove_invalid_chars)
        cleaning_layout.addRow("Allowed characters:", self.allowed_chars_edit)
        cleaning_layout.addRow("Replace:", self.custom_replace_from)
        cleaning_layout.addRow("With:", self.custom_replace_to)
        cleaning_box.setLayout(cleaning_layout)
        options_layout.addWidget(cleaning_box)

        # Case options
        case_box = QGroupBox("Case Conversion")
        case_layout = QFormLayout()
        self.case_combo = QComboBox()
        self.case_combo.addItems(["none", "UPPERCASE", "lowercase", "TitleCase"])
        case_layout.addRow("Change case:", self.case_combo)
        case_box.setLayout(case_layout)
        options_layout.addWidget(case_box)

        # Transliteration
        transliterate_box = QGroupBox("Transliteration")
        transliterate_layout = QFormLayout()
        self.transliterate = QCheckBox("Transliterate non-ASCII to ASCII")
        transliterate_layout.addRow(self.transliterate)
        transliterate_box.setLayout(transliterate_layout)
        options_layout.addWidget(transliterate_box)

        # SQL-safe options
        sql_box = QGroupBox("SQL-Safe Identifiers (Headers)")
        sql_layout = QFormLayout()
        self.sql_safe_checkbox = QCheckBox("Make headers SQL-safe")
        self.deduplicate_headers = QCheckBox("Deduplicate headers")
        sql_layout.addRow(self.sql_safe_checkbox)
        sql_layout.addRow(self.deduplicate_headers)
        sql_box.setLayout(sql_layout)
        options_layout.addWidget(sql_box)

        options_layout.addStretch()
        options_widget.setLayout(options_layout)
        dock_widget.setWidget(options_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_widget)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()