from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

class TablePreviewDialog(QDialog):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Table Preview")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFontFamily("monospace")
        layout.addWidget(self.text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.text_edit.setText(self.format_as_table(data, headers))

    def format_as_table(self, data, headers):
        if not data:
            return "No data to display."

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in data:
            for i, cell in enumerate(row):
                if len(str(cell)) > col_widths[i]:
                    col_widths[i] = len(str(cell))

        # Create the table string
        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        data_lines = [
            " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
            for row in data
        ]

        return "\n".join([header_line, separator] + data_lines)