import pandas as pd
import os
from PyQt6.QtCore import QObject, pyqtSignal

class ExcelConverter(QObject):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files, output_dir, delimiter):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.delimiter = delimiter
        self.is_running = True

    def run(self):
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            if not self.is_running:
                break
            try:
                self.log_message.emit(f"Processing {file_path}...")
                excel_name = os.path.splitext(os.path.basename(file_path))[0]
                excel_output_dir = os.path.join(self.output_dir, excel_name)
                os.makedirs(excel_output_dir, exist_ok=True)

                xls = pd.ExcelFile(file_path)
                sheets = xls.sheet_names

                total_sheets = len(sheets)
                for j, sheet_name in enumerate(sheets):
                    self.log_message.emit(f"  Exporting sheet: {sheet_name}")
                    df = pd.read_excel(xls, sheet_name=sheet_name)

                    ext = ".tsv" if self.delimiter == '\t' else ".csv"
                    output_path = os.path.join(excel_output_dir, f"{sheet_name}{ext}")

                    df.to_csv(output_path, sep=self.delimiter, index=False)

                    progress = int(((i * total_sheets + (j + 1)) / (total_files * total_sheets)) * 100)
                    self.progress_updated.emit(progress)

                self.log_message.emit(f"Finished processing {file_path}.")
            except Exception as e:
                self.log_message.emit(f"Error processing {file_path}: {e}")

        self.progress_updated.emit(100)
        self.finished.emit()

    def stop(self):
        self.is_running = False