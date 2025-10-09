import fitz  # PyMuPDF
from PyQt6.QtCore import QObject, pyqtSignal

class ImagesToPdfConverter(QObject):
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, files, output_path, orientation):
        super().__init__()
        self.files = files
        self.output_path = output_path
        self.orientation = orientation
        self.is_running = True

    def run(self):
        try:
            self.log_message.emit("Starting image to PDF conversion...")
            doc = fitz.open()
            total_files = len(self.files)

            for i, img_path in enumerate(self.files):
                if not self.is_running:
                    self.log_message.emit("Conversion cancelled.")
                    break

                self.log_message.emit(f"  Processing {img_path}...")
                img_doc = fitz.open(img_path)
                rect = img_doc[0].rect

                # Determine page size based on orientation
                if self.orientation == "Landscape":
                    page_rect = fitz.Rect(0, 0, max(rect.width, rect.height), min(rect.width, rect.height))
                else: # Portrait
                    page_rect = fitz.Rect(0, 0, min(rect.width, rect.height), max(rect.width, rect.height))

                page = doc.new_page(width=page_rect.width, height=page_rect.height)
                page.insert_image(page_rect, filename=img_path)

                progress = int(((i + 1) / total_files) * 100)
                self.progress_updated.emit(progress)

            if self.is_running:
                doc.save(self.output_path)
                self.log_message.emit(f"Successfully created PDF: {self.output_path}")

            doc.close()
        except Exception as e:
            self.log_message.emit(f"Error during image to PDF conversion: {e}")

        self.finished.emit()

    def stop(self):
        self.is_running = False