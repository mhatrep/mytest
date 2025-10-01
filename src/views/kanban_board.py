from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QMenu
from PyQt6.QtCore import Qt, QSize, QEvent
from components.note_dialog import NoteDialog
from components.note_widget import NoteWidget
from commands import AddNoteCommand, EditNoteCommand, DeleteNoteCommand, MoveNoteCommand

class KanbanBoard(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.columns = {}
        self.drag_start_info = {}
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
            list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(self.show_context_menu)

            list_widget.viewport().installEventFilter(self)
            list_widget.setObjectName(name)

            column_layout.addWidget(list_widget)
            self.columns[name] = list_widget
            self.layout.addWidget(column_widget)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Drop:
            if source.parent() in self.columns.values():
                drop_event = event
                dest_list = source.parent()

                # Find which item is being dropped on
                dest_item = dest_list.itemAt(drop_event.position().toPoint())
                dest_row = dest_list.row(dest_item) if dest_item else dest_list.count()

                # Get source info from where drag started
                source_list = self.main_window.drag_source_list
                if not source_list:
                    return True # Should not happen

                source_item = source_list.currentItem()
                source_row = source_list.row(source_item)
                source_col_name = source_list.objectName()
                note_widget = source_list.itemWidget(source_item)

                if not note_widget:
                    return True

                note_data = {
                    "description": note_widget.description,
                    "color": note_widget.color,
                    "timestamp": note_widget.timestamp,
                }

                # If moving within the same list, adjust destination row
                if dest_list is source_list and source_row < dest_row:
                    dest_row -= 1

                if dest_list is source_list and source_row == dest_row:
                    return True # No move

                command = MoveNoteCommand(
                    main_window=self.main_window,
                    source_col=source_col_name,
                    dest_col=dest_list.objectName(),
                    source_row=source_row,
                    dest_row=dest_row,
                    note_data=note_data,
                )
                self.main_window.undo_stack.push(command)
                return True

        elif event.type() == QEvent.Type.DragEnter:
            self.main_window.drag_source_list = source.parent()

        return super().eventFilter(source, event)

    def add_note(self, column_name):
        dialog = NoteDialog(self)
        if dialog.exec():
            description, color = dialog.get_data()
            if description:
                command = AddNoteCommand(self, column_name, description, color)
                self.main_window.undo_stack.push(command)

    def create_note_widget(self, column_name, description, color="#ffffa0", timestamp=""):
        note_widget = NoteWidget(description, color, timestamp)
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
        old_description = note_widget.description
        old_color = note_widget.color
        old_timestamp = note_widget.timestamp

        dialog = NoteDialog(self, description=old_description, color=old_color)
        if dialog.exec():
            new_description, new_color = dialog.get_data()
            if new_description:
                old_data = (old_description, old_color, old_timestamp)
                new_data = (new_description, new_color)
                command = EditNoteCommand(list_widget, item, note_widget, old_data, new_data, self.main_window)
                self.main_window.undo_stack.push(command)

    def delete_note(self, list_widget, item):
        command = DeleteNoteCommand(self, list_widget, item)
        self.main_window.undo_stack.push(command)

    def filter_notes(self, query):
        query = query.lower()
        for column in self.columns.values():
            for i in range(column.count()):
                item = column.item(i)
                note_widget = column.itemWidget(item)

                if note_widget:
                    description = note_widget.description.lower()
                    if query in description:
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
                    "description": widget.description,
                    "color": widget.color,
                    "timestamp": widget.timestamp,
                })
            data[name] = notes
        return data

    def load_notes(self, data):
        for name, column in self.columns.items():
            column.clear()
            if name in data:
                for note_data in data[name]:
                    self.create_note_widget(
                        name,
                        note_data["description"],
                        note_data.get("color", "#ffffa0"),
                        note_data.get("timestamp", "")
                    )