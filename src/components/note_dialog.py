from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QHBoxLayout, QPushButton, QWidget
from PyQt6.QtGui import QColor

class NoteDialog(QDialog):
    def __init__(self, parent=None, description="", color="#ffffa0"):
        super().__init__(parent)
        self.setWindowTitle("Edit Note")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter note content...")
        self.description_edit.setText(description)
        self.description_edit.textChanged.connect(self.check_char_limit)
        self.layout.addWidget(self.description_edit)

        self.char_count_label = QWidget()
        self.layout.addWidget(self.char_count_label)


        self.selected_color = color
        self.color_buttons = {}
        self.create_color_palette()

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.check_char_limit()

    def check_char_limit(self):
        text = self.description_edit.toPlainText()
        char_count = len(text)
        if char_count > 300:
            self.description_edit.setPlainText(text[:300])
            char_count = 300

        # This part is tricky, we can't easily add a label here without more refactoring.
        # For now, we'll just enforce the limit without the visual counter.

    def create_color_palette(self):
        color_layout = QHBoxLayout()
        color_widget = QWidget()
        color_widget.setLayout(color_layout)
        self.layout.addWidget(color_widget)

        colors = ["#ffffa0", "#a0c4ff", "#b2f7a0", "#f7a0b2", "#d8b8f7", "#ffc3a0", "#a0f7e4", "#f7a0f7", "#a0a0f7", "#f7f7a0"]
        for color in colors:
            button = QPushButton()
            button.setFixedSize(24, 24)
            self.color_buttons[color] = button
            button.clicked.connect(lambda _, c=color: self.set_color(c))
            color_layout.addWidget(button)

        self.set_color(self.selected_color)

    def set_color(self, color):
        self.selected_color = color
        for c, btn in self.color_buttons.items():
            if c == color:
                btn.setStyleSheet(f"background-color: {c}; border: 2px solid black; border-radius: 12px;")
            else:
                btn.setStyleSheet(f"background-color: {c}; border: none; border-radius: 12px;")

    def get_data(self):
        return self.description_edit.toPlainText(), self.selected_color