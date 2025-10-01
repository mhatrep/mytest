from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class SearchResultWidget(QWidget):
    def __init__(self, description, date_str, color):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.description_label = QLabel(description)
        self.description_label.setWordWrap(True)
        self.layout.addWidget(self.description_label)

        self.date_label = QLabel(date_str)
        font = self.date_label.font()
        font.setPointSize(8)
        self.date_label.setFont(font)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.date_label)

        self.setStyleSheet(f"""
            SearchResultWidget {{
                background-color: {color};
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }}
        """)