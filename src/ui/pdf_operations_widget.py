from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QStackedWidget
from .pdf_to_image_converter_widget import PdfToImageConverterWidget
from .pdf_merger_widget import PdfMergerWidget
from .images_to_pdf_converter_widget import ImagesToPdfConverterWidget

class PdfOperationsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.operation_combo = QComboBox()
        self.operation_combo.addItems(["PDF to Image", "PDF Merge", "Images to PDF"])
        self.layout.addWidget(self.operation_combo)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        self.pdf_to_image_widget = PdfToImageConverterWidget()
        self.pdf_merger_widget = PdfMergerWidget()
        self.images_to_pdf_widget = ImagesToPdfConverterWidget()

        self.stacked_widget.addWidget(self.pdf_to_image_widget)
        self.stacked_widget.addWidget(self.pdf_merger_widget)
        self.stacked_widget.addWidget(self.images_to_pdf_widget)

        self.operation_combo.currentIndexChanged.connect(self.stacked_widget.setCurrentIndex)