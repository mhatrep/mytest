from PyQt6.QtGui import QUndoCommand
from PyQt6.QtWidgets import QListWidgetItem
from components.note_widget import NoteWidget

class AddNoteCommand(QUndoCommand):
    def __init__(self, kanban_board, column_name, title, description, color):
        super().__init__()
        self.kanban_board = kanban_board
        self.column_name = column_name
        self.title = title
        self.description = description
        self.color = color
        self.list_item = None
        self.note_widget = None

    def redo(self):
        if not self.list_item:
            self.note_widget = NoteWidget(self.title, self.description, self.color)
            self.list_item = QListWidgetItem()
            self.list_item.setSizeHint(self.note_widget.sizeHint())

        column = self.kanban_board.columns[self.column_name]
        column.addItem(self.list_item)
        column.setItemWidget(self.list_item, self.note_widget)
        self.kanban_board.main_window.save_current_board()

    def undo(self):
        column = self.kanban_board.columns[self.column_name]
        column.takeItem(column.row(self.list_item))
        self.kanban_board.main_window.save_current_board()

class DeleteNoteCommand(QUndoCommand):
    def __init__(self, kanban_board, list_widget, item):
        super().__init__()
        self.kanban_board = kanban_board
        self.list_widget = list_widget
        self.item = item
        self.row = list_widget.row(item)
        self.widget = list_widget.itemWidget(item)

    def redo(self):
        self.list_widget.takeItem(self.row)
        self.kanban_board.main_window.save_current_board()

    def undo(self):
        self.list_widget.insertItem(self.row, self.item)
        self.list_widget.setItemWidget(self.item, self.widget)
        self.kanban_board.main_window.save_current_board()

class EditNoteCommand(QUndoCommand):
    def __init__(self, note_widget, old_data, new_data, main_window):
        super().__init__()
        self.note_widget = note_widget
        self.old_title, self.old_description, self.old_color = old_data
        self.new_title, self.new_description, self.new_color = new_data
        self.main_window = main_window

    def redo(self):
        self.note_widget.title_label.setText(self.new_title)
        self.note_widget.description_label.setText(self.new_description)
        self.note_widget.set_color(self.new_color)
        self.main_window.save_current_board()

    def undo(self):
        self.note_widget.title_label.setText(self.old_title)
        self.note_widget.description_label.setText(self.old_description)
        self.note_widget.set_color(self.old_color)
        self.main_window.save_current_board()