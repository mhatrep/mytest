from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtGui import QColor

from .constants import NUM_ROWS, NUM_COLS, SEARCH_HIGHLIGHT_COLOR

class GridModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self.highlighted_cells = set()

    def rowCount(self, parent=QModelIndex()):
        return NUM_ROWS

    def columnCount(self, parent=QModelIndex()):
        return NUM_COLS

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row, col = index.row(), index.column()
        cell_index = row * NUM_COLS + col
        if cell_index >= len(self._data): return None

        cell_data = self._data[cell_index]

        if role == Qt.ItemDataRole.BackgroundRole:
            if cell_index in self.highlighted_cells:
                return SEARCH_HIGHLIGHT_COLOR
            return QColor(cell_data.get('color', 'white'))

        if role == Qt.ItemDataRole.DisplayRole:
            return cell_data.get('title', '')

        if role == Qt.ItemDataRole.ForegroundRole:
            if cell_index in self.highlighted_cells:
                return QColor("black")

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        # This is now handled by set_cell_data
        return False

    def set_cell_data(self, index, title, content):
        if not index.isValid(): return
        row, col = index.row(), index.column()
        cell_index = row * NUM_COLS + col
        if cell_index >= len(self._data): return

        self._data[cell_index]['title'] = title
        self._data[cell_index]['content'] = content
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

    def set_color(self, index, color):
        if not index.isValid(): return
        row, col = index.row(), index.column()
        cell_index = row * NUM_COLS + col
        if cell_index >= len(self._data): return
        self._data[cell_index]['color'] = color
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])

    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def load_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

    def set_highlights(self, indices):
        self.highlighted_cells = indices
        top_left = self.index(0, 0)
        bottom_right = self.index(NUM_ROWS - 1, NUM_COLS - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ForegroundRole])
