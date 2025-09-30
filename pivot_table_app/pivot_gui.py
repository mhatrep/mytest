import sys
import pandas as pd
from PySide6.QtCore import Qt, QMimeData, Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem, QDrag, QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTableView, QPushButton, QFileDialog, QListWidgetItem,
    QAbstractItemView, QLabel, QComboBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QDialog, QDialogButtonBox
)

class FieldList(QListWidget):
    """ The main list of available fields. Only allows dragging out (copying). """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)

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
    items_changed = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # This allows drops from FieldList (copy) and other DropLists (move)
            super().dropEvent(event)
            self.items_changed.emit()

class ValuesTable(QTableWidget):
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
        self.setCellWidget(row_position, 1, combo)
        self.items_changed.emit()

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

        self.rows_list.items_changed.connect(self.repopulate_field_list)
        self.cols_list.items_changed.connect(self.repopulate_field_list)
        self.filters_list.items_changed.connect(self.repopulate_field_list)
        self.values_table.items_changed.connect(self.repopulate_field_list)

        self.totals_checkbox = QCheckBox("Show Grand Totals")
        self.totals_checkbox.setChecked(True)
        self.table_view = QTableView()
        self.load_button = QPushButton("Load CSV")
        self.load_button.clicked.connect(self.load_csv)
        self.pivot_button = QPushButton("Create Pivot Table")
        self.pivot_button.clicked.connect(self.create_pivot_table)

    def create_layout(self):
        config_layout = QVBoxLayout()
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

    def repopulate_field_list(self):
        used_fields = set()
        for i in range(self.rows_list.count()): used_fields.add(self.rows_list.item(i).text())
        for i in range(self.cols_list.count()): used_fields.add(self.cols_list.item(i).text())
        for i in range(self.filters_list.count()): used_fields.add(self.filters_list.item(i).text())
        value_fields, _ = self.values_table.get_fields_and_aggs()
        used_fields.update(value_fields)

        self.field_list.clear()
        for field in self.all_fields:
            if field not in used_fields:
                self.field_list.addItem(field)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load CSV", "", "CSV files (*.csv)")
        if path:
            try:
                self.df = pd.read_csv(path)
                self.all_fields = self.df.columns.tolist()
                for w in [self.rows_list, self.cols_list, self.filters_list]: w.clear()
                self.values_table.setRowCount(0)
                self.repopulate_field_list()
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
        else:
            if field_name in self.filters:
                del self.filters[field_name]
                item.setForeground(QApplication.style().standardPalette().color(self.foregroundRole()))

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