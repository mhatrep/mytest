from PyQt6.QtWidgets import QListWidget
from PyQt6.QtCore import Qt

class DroppableListWidget(QListWidget):
    def __init__(self, main_window, column_name):
        super().__init__()
        self.main_window = main_window
        self.column_name = column_name
        self.setDragDropMode(QListWidget.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

    def dropEvent(self, event):
        source_widget = event.source()

        if isinstance(source_widget, DroppableListWidget):
            # Get source info
            source_item = source_widget.currentItem()
            source_row = source_widget.row(source_item)
            source_column_name = source_widget.column_name
            note_widget = source_widget.itemWidget(source_item)
            note_data = {
                "title": note_widget.title_label.text(),
                "description": note_widget.description_label.text(),
                "color": note_widget.color,
            }

            # Get destination info
            dest_item = self.itemAt(event.position().toPoint())
            dest_row = self.row(dest_item) if dest_item else self.count()

            # Adjust destination row for internal moves
            if source_widget is self and source_row < dest_row:
                dest_row -= 1

            if source_widget is self and source_row == dest_row:
                event.ignore()
                return

            # Prevent default drop logic, command will handle it
            event.ignore()

            from commands import MoveNoteCommand
            command = MoveNoteCommand(
                main_window=self.main_window,
                source_col=source_column_name,
                dest_col=self.column_name,
                source_row=source_row,
                dest_row=dest_row,
                note_data=note_data,
            )
            self.main_window.undo_stack.push(command)
        else:
            super().dropEvent(event)