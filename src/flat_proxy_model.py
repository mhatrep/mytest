from PyQt6.QtCore import QAbstractProxyModel, QModelIndex, Qt

class FlatProxyModel(QAbstractProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._row_map = []
        self._source_model = None

    def setSourceModel(self, sourceModel):
        if self._source_model:
            self._source_model.modelReset.disconnect(self.reset)

        self._source_model = sourceModel
        super().setSourceModel(sourceModel)

        if self._source_model:
            self._source_model.modelReset.connect(self.reset)
            self.reset()

    def mapToSource(self, proxyIndex):
        if not proxyIndex.isValid() or proxyIndex.row() >= len(self._row_map):
            return QModelIndex()
        return self._row_map[proxyIndex.row()]

    def mapFromSource(self, sourceIndex):
        if not sourceIndex.isValid():
            return QModelIndex()

        try:
            row = self._row_map.index(sourceIndex)
            return self.createIndex(row, sourceIndex.column())
        except ValueError:
            return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self._row_map)

    def columnCount(self, parent=QModelIndex()):
        return self._source_model.columnCount(QModelIndex()) if self._source_model else 0

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        return self.createIndex(row, column)

    def parent(self, child):
        return QModelIndex()

    def reset(self):
        self.beginResetModel()
        self._row_map = []
        if self._source_model:
            self._flatten_recursive(QModelIndex())
        self.endResetModel()

    def _flatten_recursive(self, parent_index):
        rows = self._source_model.rowCount(parent_index)
        for r in range(rows):
            child_index = self._source_model.index(r, 0, parent_index)
            self._row_map.append(child_index)
            if self._source_model.hasChildren(child_index):
                self._flatten_recursive(child_index)