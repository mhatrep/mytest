from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QFontDialog, QLabel, QDialogButtonBox
from PyQt6.QtGui import QFont

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_font=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.font = current_font if current_font else QFont()
        self.font_label = QLabel(f"Current Font: {self.font.family()}, {self.font.pointSize()}pt")
        self.layout.addWidget(self.font_label)

        self.change_font_button = QPushButton("Change Font")
        self.change_font_button.clicked.connect(self.change_font)
        self.layout.addWidget(self.change_font_button)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def change_font(self):
        ok, font = QFontDialog.getFont(self.font, self)
        if ok:
            self.font = font
            self.font_label.setText(f"Current Font: {self.font.family()}, {self.font.pointSize()}pt")

    def get_font(self):
        return self.font