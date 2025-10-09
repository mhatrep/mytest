import fitz as pymupdf  # PyMuPDF
import os
from PyQt6.QtCore import QObject, pyqtSignal

class PdfToImageConverter(QObject):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files, output_dir, page_range_str, image_format, dpi):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.page_range_str = page_range_str
        self.image_format = image_format
        self.dpi = dpi
        self.is_running = True

    def parse_page_range(self, page_range_str, max_pages):
        if not page_range_str:
            return range(max_pages)

        pages = set()
        try:
            for part in page_range_str.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    pages.update(range(start - 1, end))
                else:
                    pages.add(int(part) - 1)
            return sorted([p for p in pages if 0 <= p < max_pages])
        except ValueError:
            self.log_message.emit(f"Invalid page range format: {page_range_str}")
            return []

    def run(self):
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            if not self.is_running:
                break
            try:
                self.log_message.emit(f"Processing {file_path}...")
                pdf_name = os.path.splitext(os.path.basename(file_path))[0]
                pdf_output_dir = os.path.join(self.output_dir, pdf_name)
                os.makedirs(pdf_output_dir, exist_ok=True)

                doc = pymupdf.open(file_path)
                pages_to_convert = self.parse_page_range(self.page_range_str, len(doc))

                total_pages = len(pages_to_convert)
                for j, page_num in enumerate(pages_to_convert):
                    page = doc.load_page(page_num)
                    pix = page.get_pixmap(dpi=self.dpi)
                    output_path = os.path.join(pdf_output_dir, f"page_{page_num + 1:03}.{self.image_format}")
                    pix.save(output_path)

                    progress = int(((i * total_pages + (j + 1)) / (total_files * total_pages)) * 100)
                    self.progress_updated.emit(progress)

                doc.close()
                self.log_message.emit(f"Finished processing {file_path}.")
            except Exception as e:
                self.log_message.emit(f"Error processing {file_path}: {e}")

        self.progress_updated.emit(100)
        self.finished.emit()

    def stop(self):
        self.is_running = False