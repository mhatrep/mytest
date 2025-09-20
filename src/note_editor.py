from PyQt6.QtWidgets import (QDialog, QLineEdit, QTextEdit, QVBoxLayout, QDialogButtonBox)
from PyQt6.QtGui import QFont

class NoteEditorDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Note")

        self.title_edit = QLineEdit(title)

        self.content_edit = QTextEdit()
        default_font = QFont("Consolas", 14)
        self.content_edit.setFont(default_font)
        self.content_edit.setHtml(content)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.title_edit)
        layout.addWidget(self.content_edit)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_data(self):
        return self.title_edit.text(), self.content_edit.toHtml()
