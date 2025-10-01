from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QDialogButtonBox

class NoteDialog(QDialog):
    def __init__(self, parent=None, title="", description=""):
        super().__init__(parent)
        self.setWindowTitle("Note")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_edit = QLineEdit(title)
        self.title_edit.setPlaceholderText("Title")
        self.layout.addWidget(self.title_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Description")
        if description:
            self.description_edit.setText(description)
        self.layout.addWidget(self.description_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        return self.title_edit.text(), self.description_edit.toPlainText()