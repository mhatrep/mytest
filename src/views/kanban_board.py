from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, QSize
from components.note_dialog import NoteDialog
from components.note_widget import NoteWidget
from commands import AddNoteCommand, EditNoteCommand, DeleteNoteCommand

class KanbanBoard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.columns = {}
        column_names = ["Backlog", "To Do", "In Progress", "Done"]

        for name in column_names:
            column_widget = QWidget()
            column_layout = QVBoxLayout()
            column_widget.setLayout(column_layout)

            title = QLabel(name)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column_layout.addWidget(title)

            add_button = QPushButton("+")
            add_button.clicked.connect(lambda _, n=name: self.add_note(n))
            column_layout.addWidget(add_button)

            list_widget = QListWidget()
            list_widget.setDragDropMode(QListWidget.DragDropMode.DragDrop)
            list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
            list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
            list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(self.show_context_menu)
            list_widget.model().rowsMoved.connect(self.main_window.save_current_board)
            column_layout.addWidget(list_widget)

            self.columns[name] = list_widget
            self.layout.addWidget(column_widget)

    def add_note(self, column_name):
        dialog = NoteDialog(self)
        if dialog.exec():
            title, description = dialog.get_data()
            if title:
                command = AddNoteCommand(self, column_name, title, description)
                self.main_window.undo_stack.push(command)

    def create_note_widget(self, column_name, title, description):
        note_widget = NoteWidget(title, description)
        list_item = QListWidgetItem()
        list_item.setSizeHint(note_widget.sizeHint())

        column = self.columns[column_name]
        column.addItem(list_item)
        column.setItemWidget(list_item, note_widget)
        return list_item

    def show_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")

        action = menu.exec(list_widget.mapToGlobal(pos))

        if action == edit_action:
            self.edit_note(list_widget, item)
        elif action == delete_action:
            self.delete_note(list_widget, item)

    def edit_note(self, list_widget, item):
        note_widget = list_widget.itemWidget(item)
        old_title = note_widget.title_label.text()
        old_description = note_widget.description_label.text()

        dialog = NoteDialog(self, title=old_title, description=old_description)
        if dialog.exec():
            new_title, new_description = dialog.get_data()
            if new_title:
                command = EditNoteCommand(note_widget, old_title, old_description, new_title, new_description, self.main_window)
                self.main_window.undo_stack.push(command)

    def delete_note(self, list_widget, item):
        command = DeleteNoteCommand(self, list_widget, item)
        self.main_window.undo_stack.push(command)

    def filter_notes(self, query):
        query = query.lower()
        for name, column in self.columns.items():
            for i in range(column.count()):
                item = column.item(i)
                widget = column.itemWidget(item)
                title = widget.title_label.text().lower()
                description = widget.description_label.text().lower()
                if query in title or query in description:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def get_notes(self):
        data = {}
        for name, column in self.columns.items():
            notes = []
            for i in range(column.count()):
                item = column.item(i)
                widget = column.itemWidget(item)
                notes.append({
                    "title": widget.title_label.text(),
                    "description": widget.description_label.text()
                })
            data[name] = notes
        return data

    def load_notes(self, data):
        for name, column in self.columns.items():
            column.clear()
            if name in data:
                for note_data in data[name]:
                    self.create_note_widget(name, note_data["title"], note_data["description"])