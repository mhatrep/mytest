import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QTreeView, QLineEdit, QToolBar, QListWidget
from PyQt6.QtGui import QAction, QUndoStack, QFont
from PyQt6.QtCore import Qt, QDate
from models.date_tree_model import DateTreeModel
from components.settings_dialog import SettingsDialog
from views.kanban_board import KanbanBoard
from commands import RescheduleNoteCommand
import data_manager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Planner")
        self.setGeometry(100, 100, 1200, 800)
        self.current_date = QDate.currentDate()
        self.undo_stack = QUndoStack(self)
        self.data = data_manager.load_data()
        self.load_settings()

        # Create the splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        self.create_menus()
        self.create_toolbar()

        # Left pane: Date Tree
        self.date_tree = QTreeView()
        self.date_tree.setAcceptDrops(True)
        self.date_tree.dragEnterEvent = self.tree_drag_enter_event
        self.date_tree.dropEvent = self.tree_drop_event
        self.date_tree_model = DateTreeModel()
        self.date_tree.setModel(self.date_tree_model)
        self.date_tree.clicked.connect(self.on_date_tree_clicked)
        self.splitter.addWidget(self.date_tree)

        # Right pane: Kanban Board
        self.kanban_board = KanbanBoard(self)
        self.splitter.addWidget(self.kanban_board)

        # Set initial sizes
        self.splitter.setSizes([200, 1000])
        self.load_board_for_date(self.current_date)

    def closeEvent(self, event):
        self.save_settings()
        data_manager.save_data(self.data)
        event.accept()

    def create_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)

        edit_menu = menu_bar.addMenu("Edit")

        undo_action = self.undo_stack.createUndoAction(self, "Undo")
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)

        redo_action = self.undo_stack.createRedoAction(self, "Redo")
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)

    def load_settings(self):
        settings = self.data.get("settings", {})
        font_str = settings.get("font")
        font = QFont()
        if font_str:
            font.fromString(font_str)
        else:
            font.setPointSize(14)
        QApplication.instance().setFont(font)

    def save_settings(self):
        if "settings" not in self.data:
            self.data["settings"] = {}
        self.data["settings"]["font"] = QApplication.instance().font().toString()

    def open_settings_dialog(self):
        dialog = SettingsDialog(self, current_font=QApplication.instance().font())
        if dialog.exec():
            font = dialog.get_font()
            QApplication.instance().setFont(font)

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search notes...")
        self.search_bar.textChanged.connect(self.on_search_query_changed)
        toolbar.addWidget(self.search_bar)

    def on_search_query_changed(self, query):
        self.kanban_board.filter_notes(query)

    def on_date_tree_clicked(self, index):
        item = self.date_tree_model.itemFromIndex(index)
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, QDate):
            self.current_date = data
            self.load_board_for_date(self.current_date)
        elif isinstance(data, tuple):
            # It's a month item. Populate if it hasn't been populated.
            if item.rowCount() == 0:
                year, month = data
                self.date_tree_model.add_days(item, year, month)

    def load_board_for_date(self, date):
        date_str = date.toString("yyyy-MM-dd")
        notes = self.data.get(date_str, {})
        self.kanban_board.load_notes(notes)
        if hasattr(self, 'search_bar'):
            self.on_search_query_changed(self.search_bar.text())

    def sync_data_from_board(self):
        date_str = self.current_date.toString("yyyy-MM-dd")
        self.data[date_str] = self.kanban_board.get_notes()

    def tree_drag_enter_event(self, event):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def tree_drop_event(self, event):
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.ignore()
            return

        source_list = event.source()
        if not isinstance(source_list, QListWidget) or source_list not in self.kanban_board.columns.values():
            event.ignore()
            return

        index = self.date_tree.indexAt(event.position().toPoint())
        tree_item = self.date_tree_model.itemFromIndex(index)

        if not tree_item or tree_item.hasChildren():
            event.ignore()
            return

        target_date = tree_item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(target_date, QDate) or target_date == self.current_date:
            event.ignore()
            return

        event.accept()

        dragged_item = source_list.selectedItems()[0]
        source_row = source_list.row(dragged_item)
        note_widget = source_list.itemWidget(dragged_item)
        note_data = {
            "title": note_widget.title,
            "description": note_widget.description,
            "color": note_widget.color,
            "timestamp": note_widget.timestamp,
        }

        source_column_name = ""
        for name, column in self.kanban_board.columns.items():
            if column is source_list:
                source_column_name = name
                break

        command = RescheduleNoteCommand(
            main_window=self,
            source_column_name=source_column_name,
            source_row=source_row,
            note_data=note_data,
            source_date=self.current_date,
            target_date=target_date,
        )
        self.undo_stack.push(command)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())