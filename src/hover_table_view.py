from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QTableView, QLabel, QApplication

from .constants import NUM_COLS

class HoverTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.last_hovered_index = None

        self.preview_label = QLabel(self, Qt.WindowType.ToolTip)
        self.preview_label.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.preview_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.preview_label.setStyleSheet("""
            background-color: #f0f0f0;
            color: black;
            border: 1px solid black;
            padding: 4px;
            border-radius: 3px;
        """)
        self.preview_label.hide()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        index = self.indexAt(event.pos())

        if index.isValid() and index != self.last_hovered_index:
            self.last_hovered_index = index

            cell_index = index.row() * NUM_COLS + index.column()
            content_html = self.model()._data[cell_index].get('content', '')

            if content_html:
                temp_doc = QTextDocument()
                temp_doc.setHtml(content_html)
                QApplication.clipboard().setText(temp_doc.toPlainText())

                self.preview_label.setText(content_html)
                self.preview_label.adjustSize()

                pos = event.globalPosition().toPoint()
                pos.setX(pos.x() + 10)
                pos.setY(pos.y() + 10)
                self.preview_label.move(pos)
                self.preview_label.show()
            else:
                self.preview_label.hide()
        elif not index.isValid():
            self.last_hovered_index = None
            self.preview_label.hide()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.last_hovered_index = None
        self.preview_label.hide()
