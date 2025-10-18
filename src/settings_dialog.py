from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QComboBox, QDialogButtonBox
)

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.delimiter_input = QLineEdit(settings.get("csv_delimiter", ","))
        form_layout.addRow("CSV Delimiter:", self.delimiter_input)

        self.max_cell_width_input = QSpinBox()
        self.max_cell_width_input.setRange(10, 1000)
        self.max_cell_width_input.setValue(settings.get("max_cell_width", 100))
        form_layout.addRow("Max Cell Width:", self.max_cell_width_input)

        self.null_format_input = QLineEdit(settings.get("null_format", "NULL"))
        form_layout.addRow("Null Formatting:", self.null_format_input)

        self.bool_format_input = QComboBox()
        self.bool_format_input.addItems(["True/False", "true/false", "1/0"])
        self.bool_format_input.setCurrentText(settings.get("bool_format", "True/False"))
        form_layout.addRow("Boolean Formatting:", self.bool_format_input)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_settings(self):
        return {
            "csv_delimiter": self.delimiter_input.text(),
            "max_cell_width": self.max_cell_width_input.value(),
            "null_format": self.null_format_input.text(),
            "bool_format": self.bool_format_input.currentText()
        }