import sys
import pandas as pd
from functools import partial
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QDrag, QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTableView, QPushButton, QFileDialog, QListWidgetItem,
    QAbstractItemView, QLabel, QComboBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QDialog, QDialogButtonBox, QMenu
)

class FieldList(QListWidget):
    """ The main list of available fields. Only allows dragging out (copying). """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(False)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            mime_data = QMimeData()
            mime_data.setText(item.text())
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction) # We only ever copy from this list

class DropList(QListWidget):
    """ A list that can accept drops and allows items to be moved out of it. """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            event.ignore()
            return

        source = event.source()

        # Handle reordering within the same list
        if source == self:
            super().dropEvent(event)
            return

        item_text = event.mimeData().text()

        # Prevent duplicates
        if self.findItems(item_text, Qt.MatchExactly):
            event.ignore()
            return

        # Accept the event before making changes.
        event.acceptProposedAction()

        # Manually add the item text. This is safer than calling super().dropEvent(),
        # which can have complex side-effects.
        self.addItem(item_text)

        # If the source is another DropList, remove the item from it to complete the "move"
        if isinstance(source, DropList):
            source.takeItem(source.row(source.currentItem()))

class ValuesTable(QTableWidget):
    values_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(False)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Field", "Aggregation"])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.verticalHeader().hide()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            field_name = event.mimeData().text()
            self.add_field(field_name)
            event.acceptProposedAction()
            source = event.source()
            # If the drop came from a list that supports moving, remove the source item
            if isinstance(source, DropList):
                source.takeItem(source.row(source.currentItem()))
        else:
            event.ignore()

    def add_field(self, field_name):
        if any(self.item(row, 0).text() == field_name for row in range(self.rowCount())): return
        row_position = self.rowCount()
        self.insertRow(row_position)
        self.setItem(row_position, 0, QTableWidgetItem(field_name))
        combo = QComboBox()
        combo.addItems(['sum', 'mean', 'count', 'min', 'max'])
        combo.currentTextChanged.connect(self.values_changed.emit)
        self.setCellWidget(row_position, 1, combo)
        self.values_changed.emit()

    def get_fields_and_aggs(self):
        fields, aggs = [], {}
        for row in range(self.rowCount()):
            field, agg = self.item(row, 0).text(), self.cellWidget(row, 1).currentText()
            fields.append(field)
            aggs[field] = agg
        return fields, aggs

class FilterDialog(QDialog):
    def __init__(self, field_name, values, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Filter {field_name}")
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for val in values:
            item = QListWidgetItem(str(val))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_selected_values(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count()) if self.list_widget.item(i).checkState() == Qt.Checked]

class PivotTableApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pivot Table Application")
        self.setGeometry(100, 100, 1200, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.df = None
        self.all_fields = []
        self.filters = {}
        self.create_widgets()
        self.create_layout()

    def create_widgets(self):
        self.field_list = FieldList()
        self.rows_list = DropList()
        self.cols_list = DropList()
        self.filters_list = DropList()
        self.filters_list.itemDoubleClicked.connect(self.open_filter_dialog)
        self.values_table = ValuesTable()

        # Setup context menus
        self.field_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.field_list.customContextMenuRequested.connect(self.show_field_list_context_menu)
        for list_widget in [self.rows_list, self.cols_list, self.filters_list]:
            list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(partial(self.show_group_list_context_menu, list_widget))

        self.totals_checkbox = QCheckBox("Show Grand Totals")
        self.totals_checkbox.setChecked(True)
        self.table_view = QTableView()
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)
        self.pivot_button = QPushButton("Create Pivot Table")
        self.pivot_button.clicked.connect(self.create_pivot_table)

        # Connect signals for automatic updates
        self.rows_list.model().rowsInserted.connect(self.create_pivot_table)
        self.rows_list.model().rowsRemoved.connect(self.create_pivot_table)
        self.cols_list.model().rowsInserted.connect(self.create_pivot_table)
        self.cols_list.model().rowsRemoved.connect(self.create_pivot_table)
        self.filters_list.model().rowsInserted.connect(self.create_pivot_table)
        self.filters_list.model().rowsRemoved.connect(self.create_pivot_table)
        self.totals_checkbox.stateChanged.connect(self.create_pivot_table)
        self.values_table.values_changed.connect(self.create_pivot_table)

    def create_layout(self):
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.load_button)
        config_layout.addWidget(QLabel("Fields (Drag from here)"))
        config_layout.addWidget(self.field_list)
        config_layout.addWidget(QLabel("Filters (Double-click to edit)"))
        config_layout.addWidget(self.filters_list)
        config_layout.addWidget(QLabel("Rows"))
        config_layout.addWidget(self.rows_list)
        config_layout.addWidget(QLabel("Columns"))
        config_layout.addWidget(self.cols_list)
        config_layout.addWidget(QLabel("Values"))
        config_layout.addWidget(self.values_table)
        config_layout.addWidget(self.totals_checkbox)
        config_layout.addWidget(self.pivot_button)
        config_layout.addStretch()

        table_layout = QVBoxLayout()
        table_layout.addWidget(self.table_view)

        main_layout = QHBoxLayout(self.central_widget)
        main_layout.addLayout(config_layout, 1)
        main_layout.addLayout(table_layout, 4)

    def add_item_to_list(self, item_text, list_widget):
        if not list_widget.findItems(item_text, Qt.MatchExactly):
            list_widget.addItem(item_text)

    def show_field_list_context_menu(self, pos):
        item = self.field_list.itemAt(pos)
        if not item:
            return

        item_text = item.text()
        menu = QMenu()
        menu.addAction("Add to Rows", partial(self.add_item_to_list, item_text, self.rows_list))
        menu.addAction("Add to Columns", partial(self.add_item_to_list, item_text, self.cols_list))
        menu.addAction("Add to Filters", partial(self.add_item_to_list, item_text, self.filters_list))
        menu.addAction("Add to Values", partial(self.values_table.add_field, item_text))
        menu.exec(self.field_list.mapToGlobal(pos))

    def show_group_list_context_menu(self, list_widget, pos):
        item = list_widget.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        menu.addAction("Remove", lambda: list_widget.takeItem(list_widget.row(item)))
        menu.exec(list_widget.mapToGlobal(pos))

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV files (*.csv)")
        if path:
            try:
                self.df = pd.read_csv(path)
                self.all_fields = self.df.columns.tolist()
                self.field_list.clear()
                self.field_list.addItems(self.all_fields)
                for w in [self.rows_list, self.cols_list, self.filters_list]: w.clear()
                self.values_table.setRowCount(0)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")

    def open_filter_dialog(self, item):
        field_name = item.text()
        if self.df is None: return
        unique_values = sorted(self.df[field_name].unique())
        dialog = FilterDialog(field_name, unique_values, self)
        if dialog.exec():
            self.filters[field_name] = dialog.get_selected_values()
            item.setForeground(QColor("blue"))
            self.create_pivot_table()
        else:
            if field_name in self.filters:
                del self.filters[field_name]
                item.setForeground(QApplication.style().standardPalette().color(self.foregroundRole()))
                self.create_pivot_table()

    def create_pivot_table(self):
        if self.df is None: return QMessageBox.warning(self, "Warning", "Please load a CSV file first.")
        rows = [self.rows_list.item(i).text() for i in range(self.rows_list.count())]
        cols = [self.cols_list.item(i).text() for i in range(self.cols_list.count())]
        values, aggfunc = self.values_table.get_fields_and_aggs()
        if not (rows or cols) and not values: return QMessageBox.warning(self, "Warning", "Please define at least one row, column, or value.")
        try:
            filtered_df = self.df.copy()
            if self.filters:
                for field, selected_values in self.filters.items():
                    if pd.api.types.is_numeric_dtype(filtered_df[field]):
                        selected_values = pd.to_numeric(selected_values, errors='coerce')
                    filtered_df = filtered_df[filtered_df[field].isin(selected_values)]
            pivot_table = filtered_df.pivot_table(index=rows, columns=cols, values=values, aggfunc=aggfunc,
                                                  margins=self.totals_checkbox.isChecked(), margins_name='Grand Total', fill_value=0)
            self.display_df(pivot_table)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create pivot table: {e}")

    def display_df(self, df):
        if df.index.name is not None or (isinstance(df.index, pd.MultiIndex) and any(name is not None for name in df.index.names)):
            df = df.reset_index()
        model = QStandardItemModel()
        font = QFont(); font.setBold(True)
        self.table_view.horizontalHeader().setFont(font)
        if isinstance(df.columns, pd.MultiIndex):
            headers = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
        else:
            headers = df.columns.tolist()
        df.columns = headers
        model.setHorizontalHeaderLabels(headers)
        total_color = QColor(220, 220, 220)
        for i in range(df.shape[0]):
            items = []
            is_total_row = 'Grand Total' in df.iloc[i].values
            for col_idx, val in enumerate(df.iloc[i].values):
                item = QStandardItem(str(val))
                if is_total_row or ('Grand Total' in str(headers[col_idx])):
                    item.setBackground(total_color)
                items.append(item)
            model.appendRow(items)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()