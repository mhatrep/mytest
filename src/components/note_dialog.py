from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QTextEdit, QDialogButtonBox, QHBoxLayout, QPushButton, QWidget
from PyQt6.QtGui import QColor

class NoteDialog(QDialog):
    def __init__(self, parent=None, title="", description="", color="#ffffa0"):
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

        self.selected_color = color
        self.create_color_palette()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def create_color_palette(self):
        color_layout = QHBoxLayout()
        color_widget = QWidget()
        color_widget.setLayout(color_layout)
        self.layout.addWidget(color_widget)

        colors = ["#ffffa0", "#a0c4ff", "#b2f7a0", "#f7a0b2", "#d8b8f7"]
        for color in colors:
            button = QPushButton()
            button.setFixedSize(24, 24)
            button.setStyleSheet(f"background-color: {color}; border-radius: 12px;")
            button.clicked.connect(lambda _, c=color: self.set_color(c))
            color_layout.addWidget(button)

    def set_color(self, color):
        self.selected_color = color

    def get_data(self):
        return self.title_edit.text(), self.description_edit.toPlainText(), self.selected_color