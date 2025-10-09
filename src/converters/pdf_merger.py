from PyPDF2 import PdfMerger as PyPdf2Merger
from PyQt6.QtCore import QObject, pyqtSignal

class PdfMerger(QObject):
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files, output_path):
        super().__init__()
        self.files = files
        self.output_path = output_path
        self.is_running = True

    def run(self):
        try:
            self.log_message.emit("Starting PDF merge...")
            merger = PyPdf2Merger()
            for pdf in self.files:
                if not self.is_running:
                    self.log_message.emit("Merge cancelled.")
                    break
                self.log_message.emit(f"  Appending {pdf}")
                merger.append(pdf)

            if self.is_running:
                merger.write(self.output_path)
                merger.close()
                self.log_message.emit(f"Successfully merged files to {self.output_path}")
        except Exception as e:
            self.log_message.emit(f"Error during PDF merging: {e}")

        self.finished.emit()

    def stop(self):
        self.is_running = False