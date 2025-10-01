from PyQt6.QtGui import QUndoCommand
from PyQt6.QtWidgets import QListWidgetItem
from components.note_widget import NoteWidget

import datetime

class AddNoteCommand(QUndoCommand):
    def __init__(self, kanban_board, column_name, title, description, color):
        super().__init__()
        self.kanban_board = kanban_board
        self.column_name = column_name
        self.title = title
        self.description = description
        self.color = color
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.list_item = None
        self.note_widget = None

    def redo(self):
        if not self.list_item:
            self.note_widget = NoteWidget(self.title, self.description, self.color, self.timestamp)
            self.list_item = QListWidgetItem()
            self.list_item.setSizeHint(self.note_widget.sizeHint())

        column = self.kanban_board.columns[self.column_name]
        column.addItem(self.list_item)
        column.setItemWidget(self.list_item, self.note_widget)
        self.kanban_board.main_window.sync_data_from_board()

    def undo(self):
        column = self.kanban_board.columns[self.column_name]
        column.takeItem(column.row(self.list_item))
        self.kanban_board.main_window.sync_data_from_board()

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
        self.kanban_board.main_window.sync_data_from_board()

    def undo(self):
        self.list_widget.insertItem(self.row, self.item)
        self.list_widget.setItemWidget(self.item, self.widget)
        self.kanban_board.main_window.sync_data_from_board()

class EditNoteCommand(QUndoCommand):
    def __init__(self, list_widget, item, note_widget, old_data, new_data, main_window):
        super().__init__()
        self.list_widget = list_widget
        self.item = item
        self.note_widget = note_widget
        self.old_title, self.old_description, self.old_color, self.old_timestamp = old_data
        self.new_title, self.new_description, self.new_color = new_data
        self.new_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.main_window = main_window

    def redo(self):
        self.note_widget.set_content(self.new_title, self.new_description, self.new_timestamp)
        self.note_widget.set_color(self.new_color)
        self.item.setSizeHint(self.note_widget.sizeHint())
        self.main_window.sync_data_from_board()

    def undo(self):
        self.note_widget.set_content(self.old_title, self.old_description, self.old_timestamp)
        self.note_widget.set_color(self.old_color)
        self.item.setSizeHint(self.note_widget.sizeHint())
        self.main_window.sync_data_from_board()

class MoveNoteCommand(QUndoCommand):
    def __init__(self, main_window, source_col, dest_col, source_row, dest_row, note_data):
        super().__init__()
        self.main_window = main_window
        self.source_col = source_col
        self.dest_col = dest_col
        self.source_row = source_row
        self.dest_row = dest_row
        self.note_data = note_data

    def redo(self):
        date_str = self.main_window.current_date.toString("yyyy-MM-dd")

        # Remove from source
        self.main_window.data[date_str][self.source_col].pop(self.source_row)

        # Add to destination
        self.main_window.data[date_str][self.dest_col].insert(self.dest_row, self.note_data)

        self.main_window.load_board_for_date(self.main_window.current_date)

    def undo(self):
        date_str = self.main_window.current_date.toString("yyyy-MM-dd")

        # Remove from destination
        self.main_window.data[date_str][self.dest_col].pop(self.dest_row)

        # Add back to source
        self.main_window.data[date_str][self.source_col].insert(self.source_row, self.note_data)

        self.main_window.load_board_for_date(self.main_window.current_date)

class RescheduleNoteCommand(QUndoCommand):
    def __init__(self, main_window, source_column_name, source_row, note_data, source_date, target_date):
        super().__init__()
        self.main_window = main_window
        self.source_column_name = source_column_name
        self.source_row = source_row
        self.note_data = note_data
        self.source_date = source_date
        self.target_date = target_date

    def redo(self):
        source_date_str = self.source_date.toString("yyyy-MM-dd")
        self.main_window.data[source_date_str][self.source_column_name].pop(self.source_row)

        target_date_str = self.target_date.toString("yyyy-MM-dd")
        if target_date_str not in self.main_window.data:
            self.main_window.data[target_date_str] = { "Backlog": [], "To Do": [], "In Progress": [], "Done": [] }
        self.main_window.data[target_date_str]["Backlog"].insert(0, self.note_data)

        if self.source_date == self.main_window.current_date:
            self.main_window.load_board_for_date(self.source_date)

    def undo(self):
        target_date_str = self.target_date.toString("yyyy-MM-dd")
        self.main_window.data[target_date_str]["Backlog"].remove(self.note_data)

        source_date_str = self.source_date.toString("yyyy-MM-dd")
        self.main_window.data[source_date_str][self.source_column_name].insert(self.source_row, self.note_data)

        if self.source_date == self.main_window.current_date:
            self.main_window.load_board_for_date(self.source_date)
        elif self.target_date == self.main_window.current_date:
            self.main_window.load_board_for_date(self.target_date)