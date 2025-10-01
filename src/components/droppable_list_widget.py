from PyQt6.QtWidgets import QListWidget
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class DroppableListWidget(QListWidget):
    def __init__(self, main_window, column_name):
        super().__init__()
        self.main_window = main_window
        self.column_name = column_name
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setAcceptDrops(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        mime_data = QMimeData()
        mime_data.setText(f"{self.objectName()},{self.row(item)}")

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(supportedActions, Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        source_mime_data = event.mimeData().text()
        if not source_mime_data:
            event.ignore()
            return

        source_col_name, source_row_str = source_mime_data.split(',')
        source_row = int(source_row_str)

        source_list = self.main_window.kanban_board.columns[source_col_name]
        source_item = source_list.item(source_row)
        note_widget = source_list.itemWidget(source_item)

        if not note_widget:
            event.ignore()
            return

        note_data = {
            "description": note_widget.description,
            "color": note_widget.color,
            "timestamp": note_widget.timestamp,
        }

        dest_item = self.itemAt(event.position().toPoint())
        dest_row = self.row(dest_item) if dest_item else self.count()

        if source_list is self and source_row < dest_row:
            dest_row -= 1

        if source_list is self and source_row == dest_row:
            event.ignore()
            return

        from commands import MoveNoteCommand
        command = MoveNoteCommand(
            main_window=self.main_window,
            source_col=source_col_name,
            dest_col=self.column_name,
            source_row=source_row,
            dest_row=dest_row,
            note_data=note_data,
        )
        self.main_window.undo_stack.push(command)
        event.accept()

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()