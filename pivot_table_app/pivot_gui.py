import sys
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QTableView,
    QPushButton,
    QFileDialog,
    QListWidgetItem,
    QAbstractItemView,
    QLabel,
    QComboBox,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem

class ValuesTableWidget(QTableWidget):
    """A QTableWidget customized for handling value fields and their aggregations."""
    items_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Field", "Aggregation"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.verticalHeader().hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            field_name = event.mimeData().text()
            self.add_field(field_name)
            event.accept()
        else:
            event.ignore()

    def add_field(self, field_name):
        """Adds a new field to the table if it's not already present."""
        for row in range(self.rowCount()):
            if self.item(row, 0).text() == field_name:
                return  # Avoid duplicates

        row_position = self.rowCount()
        self.insertRow(row_position)

        field_item = QTableWidgetItem(field_name)
        self.setItem(row_position, 0, field_item)

        agg_combo = QComboBox()
        agg_combo.addItems(['sum', 'mean', 'count', 'min', 'max'])
        self.setCellWidget(row_position, 1, agg_combo)
        self.items_changed.emit()

    def get_fields_and_aggs(self):
        """Returns a tuple of (list_of_fields, dict_of_aggregations)."""
        fields = []
        aggs = {}
        for row in range(self.rowCount()):
            field = self.item(row, 0).text()
            agg_combo = self.cellWidget(row, 1)
            agg = agg_combo.currentText()
            fields.append(field)
            aggs[field] = agg
        return fields, aggs

class PivotTableApp(QMainWindow):
    """Main application window for the Pivot Table tool."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pivot Table Application")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.df = None
        self.all_fields = []
        self.is_updating = False

        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        """Create and configure all widgets for the application."""
        def setup_list_widget(list_widget):
            """Configure a QListWidget with drag and drop properties."""
            list_widget.setDragEnabled(True)
            list_widget.setAcceptDrops(True)
            list_widget.setDragDropMode(QAbstractItemView.InternalMove)
            list_widget.setDefaultDropAction(Qt.MoveAction)
            list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.field_list = QListWidget()
        self.field_list.setDragEnabled(True)
        self.field_list.setDragDropMode(QAbstractItemView.DragOnly)


        self.rows_list = QListWidget()
        setup_list_widget(self.rows_list)

        self.cols_list = QListWidget()
        setup_list_widget(self.cols_list)

        self.values_table = ValuesTableWidget()

        # Connect signals to repopulate the field list whenever items change
        for list_widget in [self.field_list, self.rows_list, self.cols_list]:
            list_widget.model().rowsInserted.connect(self.repopulate_field_list)
            list_widget.model().rowsRemoved.connect(self.repopulate_field_list)
        self.values_table.items_changed.connect(self.repopulate_field_list)

        self.table_view = QTableView()
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)

        self.pivot_button = QPushButton("Create Pivot Table")
        self.pivot_button.clicked.connect(self.create_pivot_table)

    def create_layout(self):
        """Set up the layout for the main window."""
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.load_button)
        config_layout.addWidget(QLabel("Fields"))
        config_layout.addWidget(self.field_list)
        config_layout.addWidget(QLabel("Rows"))
        config_layout.addWidget(self.rows_list)
        config_layout.addWidget(QLabel("Columns"))
        config_layout.addWidget(self.cols_list)
        config_layout.addWidget(QLabel("Values"))
        config_layout.addWidget(self.values_table)
        config_layout.addWidget(self.pivot_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table_view)

        self.layout.addLayout(config_layout, 1)
        self.layout.addLayout(main_layout, 4)

    def repopulate_field_list(self):
        """Ensure the field list only contains unused fields."""
        if self.is_updating:
            return  # Prevent re-entrancy

        self.is_updating = True
        try:
            used_fields = set()
            for i in range(self.rows_list.count()):
                used_fields.add(self.rows_list.item(i).text())
            for i in range(self.cols_list.count()):
                used_fields.add(self.cols_list.item(i).text())

            value_fields, _ = self.values_table.get_fields_and_aggs()
            for field in value_fields:
                used_fields.add(field)

            self.field_list.blockSignals(True)
            self.field_list.clear()
            for field in self.all_fields:
                if field not in used_fields:
                    self.field_list.addItem(QListWidgetItem(field))
            self.field_list.blockSignals(False)
        finally:
            self.is_updating = False

    def load_csv(self):
        """Open a file dialog to load a CSV and populate the field list."""
        path, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV files (*.csv)")
        if path:
            try:
                self.df = pd.read_csv(path)
                self.all_fields = self.df.columns.tolist()
                self.rows_list.clear()
                self.cols_list.clear()
                self.values_table.setRowCount(0)
                self.repopulate_field_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")

    def create_pivot_table(self):
        """Generate and display the pivot table based on user selections."""
        if self.df is None:
            QMessageBox.warning(self, "Warning", "Please load a CSV file first.")
            return

        rows = [self.rows_list.item(i).text() for i in range(self.rows_list.count())]
        cols = [self.cols_list.item(i).text() for i in range(self.cols_list.count())]
        values = [self.values_list.item(i).text() for i in range(self.values_list.count())]

        if not rows or not values:
            QMessageBox.warning(self, "Warning", "Please define at least one row and one value.")
            return

        try:
            aggfunc = self.agg_func_combo.currentText()
            pivot_table = self.df.pivot_table(index=rows, columns=cols, values=values, aggfunc=aggfunc)
            self.display_df(pivot_table.reset_index())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create pivot table: {e}")

    def display_df(self, df):
        """Display a pandas DataFrame in the QTableView, handling multi-level headers."""
        model = QStandardItemModel()

        if isinstance(df.columns, pd.MultiIndex):
            # Flatten multi-level column headers
            headers = ['_'.join(map(str, col)).strip() for col in df.columns.values]
        else:
            headers = df.columns.tolist()

        df.columns = headers
        model.setHorizontalHeaderLabels(headers)

        for i, row in df.iterrows():
            items = [QStandardItem(str(val)) for val in row]
            model.appendRow(items)

        self.table_view.setModel(model)