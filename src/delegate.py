from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QTextDocument, QFont
from PyQt6.QtWidgets import (QStyledItemDelegate, QTextEdit, QStyleOptionViewItem, QStyle, QApplication)

class TextEditDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        painter.save()
        doc = QTextDocument()
        font = doc.defaultFont()
        font.setPointSize(12)
        doc.setDefaultFont(font)
        doc.setHtml(options.text)
        options.text = ""
        style = options.widget.style() if options.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, options, painter)
        painter.translate(options.rect.left() + 3, options.rect.top() + 3)
        clip = QRectF(0, 0, options.rect.width() - 6, options.rect.height() - 6)
        doc.drawContents(painter, clip)
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
