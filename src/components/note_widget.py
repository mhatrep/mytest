from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt6.QtCore import QSize, Qt

class NoteWidget(QWidget):
    def __init__(self, description="", color="#ffffa0", timestamp=""):
        super().__init__()
        self.color = color
        self.description = description
        self.timestamp = timestamp

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layout.addWidget(self.text_edit)
        self.setLayout(self.layout)

        self.update_display()
        self.set_color(color)

    def update_display(self):
        html_content = f"""
        <div style='padding: 5px;'>
            <p>{self.description}</p>
            <p style='font-size: 8pt; color: #888;'>{self.timestamp}</p>
        </div>
        """
        self.text_edit.setHtml(html_content)

    def set_content(self, description, timestamp):
        self.description = description
        self.timestamp = timestamp
        self.update_display()

    def set_color(self, color):
        self.color = color
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.color};
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        """)

    def sizeHint(self):
        width = 150
        self.text_edit.document().setTextWidth(width - 10) # HTML padding
        height = self.text_edit.document().size().height()
        return QSize(width, int(height) + 10) # HTML padding