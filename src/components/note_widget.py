from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QFont

class NoteWidget(QWidget):
    def __init__(self, title, description="", color="#ffffa0", timestamp=""):
        super().__init__()
        self.color = color
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)

        self.timestamp_label = QLabel(timestamp)
        font = self.timestamp_label.font()
        font.setPointSize(8)
        self.timestamp_label.setFont(font)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)
        self.layout.addStretch()
        self.layout.addWidget(self.timestamp_label)

        self.set_color(color)

    def set_color(self, color):
        self.color = color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color};
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        """)

    def sizeHint(self):
        width = 150
        margins = self.layout.contentsMargins()
        spacing = self.layout.spacing()

        title_height = self.title_label.sizeHint().height()
        description_height = self.description_label.heightForWidth(width - margins.left() - margins.right())
        timestamp_height = self.timestamp_label.sizeHint().height()

        total_height = (margins.top() + title_height + spacing +
                        description_height + spacing + timestamp_height +
                        margins.bottom())

        return QSize(width, total_height)