from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QSize

class NoteWidget(QWidget):
    def __init__(self, title, description=""):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel(title)
        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)

        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)

    def sizeHint(self):
        return QSize(150, 100)