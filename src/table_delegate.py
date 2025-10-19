from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QPainter, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QSize

class TableInCellDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("monospace", 10)
        self.font_metrics = QFontMetrics(self.font)

    def paint(self, painter, option, index):
        painter.save()

        data = index.data(Qt.ItemDataRole.DisplayRole)

        if isinstance(data, list) and all(isinstance(i, dict) for i in data):
            self.paint_table(painter, option, data)
        else:
            # For non-list data, we'll draw it as a string
            painter.drawText(option.rect, Qt.TextFlag.TextWordWrap, str(data))

        painter.restore()

    def sizeHint(self, option, index):
        data = index.data(Qt.ItemDataRole.DisplayRole)
        if isinstance(data, list) and all(isinstance(i, dict) for i in data):
            text = self.format_as_table(data)
            lines = text.split('\n')
            height = self.font_metrics.height() * len(lines)
            width = max(self.font_metrics.horizontalAdvance(line) for line in lines)
            return QSize(width, height)

        return super().sizeHint(option, index)

    def paint_table(self, painter, option, data):
        painter.fillRect(option.rect, Qt.GlobalColor.white)
        painter.setFont(self.font)

        text = self.format_as_table(data)

        # We need to draw the text line by line to get the correct layout
        rect = QRect(option.rect)
        for line in text.split('\n'):
            painter.drawText(rect, Qt.TextFlag.TextSingleLine, line)
            rect.setTop(rect.top() + self.font_metrics.height())

    def format_as_table(self, data):
        if not data:
            return ""

        headers = list(data[0].keys())
        rows = [[str(item.get(h, '')) for h in headers] for item in data]

        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if len(cell) > col_widths[i]:
                    col_widths[i] = len(cell)

        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        separator = "-+-".join("-" * w for w in col_widths)
        data_lines = [
            " | ".join(cell.ljust(w) for cell, w in zip(row, col_widths))
            for row in rows
        ]

        return "\n".join([header_line, separator] + data_lines)