import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QSplitter, QTreeView, QLineEdit, QToolBar, QListWidget
from PyQt6.QtGui import QAction, QUndoStack
from PyQt6.QtCore import Qt, QDate
from models.date_tree_model import DateTreeModel
from views.kanban_board import KanbanBoard
import data_manager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Planner")
        self.setGeometry(100, 100, 1200, 800)
        self.current_date = QDate.currentDate()
        self.undo_stack = QUndoStack(self)

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

    def create_menus(self):
        menu_bar = self.menuBar()
        edit_menu = menu_bar.addMenu("Edit")

        undo_action = self.undo_stack.createUndoAction(self, "Undo")
        undo_action.setShortcut("Ctrl+Z")
        edit_menu.addAction(undo_action)

        redo_action = self.undo_stack.createRedoAction(self, "Redo")
        redo_action.setShortcut("Ctrl+Y")
        edit_menu.addAction(redo_action)

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
            if item.childCount() == 0:
                year, month = data
                self.date_tree_model.add_days(item, year, month)

    def load_board_for_date(self, date):
        notes = data_manager.get_notes_for_date(date)
        self.kanban_board.load_notes(notes)

    def save_current_board(self):
        notes = self.kanban_board.get_notes()
        data_manager.save_notes_for_date(self.current_date, notes)

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
        note_widget = source_list.itemWidget(dragged_item)
        title = note_widget.title_label.text()
        description = note_widget.description_label.text()

        target_notes = data_manager.get_notes_for_date(target_date)
        if "Backlog" not in target_notes:
            target_notes["Backlog"] = []
        target_notes["Backlog"].append({"title": title, "description": description})
        data_manager.save_notes_for_date(target_date, target_notes)

        source_list.takeItem(source_list.row(dragged_item))
        self.save_current_board()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())