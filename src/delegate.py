from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import QTextDocument, QFont, QPen
from PyQt6.QtWidgets import (QStyledItemDelegate, QTextEdit, QStyleOptionViewItem, QStyle, QApplication)

from .constants import SEARCH_HIGHLIGHT_COLOR

class TextEditDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        painter.save()
        doc = QTextDocument()
        font = QFont("Consolas", 14)
        doc.setDefaultFont(font)
        doc.setHtml(options.text)
        doc.setDocumentMargin(0)
        options.text = ""
        style = options.widget.style() if options.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter)
        painter.translate(options.rect.left() + 3, options.rect.top() + 3)
        clip = QRectF(0, 0, options.rect.width() - 6, options.rect.height() - 6)
        doc.setTextWidth(max(0.0, clip.width()))
        doc.drawContents(painter, clip)
        painter.restore()

        model = index.model()
        if hasattr(model, "is_cell_highlighted") and model.is_cell_highlighted(index):
            painter.save()
            pen = QPen(SEARCH_HIGHLIGHT_COLOR)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            border_rect = options.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(border_rect)
            painter.restore()

    def createEditor(self, parent, option, index):
        return QTextEdit(parent)

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setHtml(value)

    def setModelData(self, editor, model, index):
        value = editor.toHtml()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        font = QFont("Consolas", 14)
        doc.setDefaultFont(font)
        doc.setHtml(options.text)
        doc.setDocumentMargin(0)

        column_width = options.rect.width()
        if options.widget:
            column_width = options.widget.columnWidth(index.column())
        if column_width <= 0:
            column_width = 100
        doc.setTextWidth(max(0.0, column_width - 6))
        size = doc.size().toSize()
        return QSize(column_width, size.height() + 6)
