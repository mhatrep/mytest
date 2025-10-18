from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

class TreeItem:
    def __init__(self, key, value, parent=None):
        self._parent = parent
        self._key = key
        self._value = value
        self._children = []

    def appendChild(self, item):
        self._children.append(item)

    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def columnCount(self):
        return 2

    def data(self, column):
        if column == 0:
            return self._key
        if column == 1:
            return str(self._value) if self._value is not None else ""
        return None

    def parent(self):
        return self._parent

    def row(self):
        if self._parent:
            return self._parent._children.index(self)
        return 0

class TreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._root_item = TreeItem("Key", "Value")
        self._setup_model_data(data, self._root_item, 0)

    def _setup_model_data(self, data, parent, depth):
        if depth > 10:
            return

        if isinstance(data, dict):
            for key, value in data.items():
                is_primitive_list = isinstance(value, list) and not any(isinstance(i, (dict, list)) for i in value)

                if is_primitive_list:
                    child_item = TreeItem(key, value, parent)
                    parent.appendChild(child_item)
                elif isinstance(value, (dict, list)):
                    child_item = TreeItem(key, None, parent)
                    parent.appendChild(child_item)
                    self._setup_model_data(value, child_item, depth + 1)
                else:
                    child_item = TreeItem(key, value, parent)
                    parent.appendChild(child_item)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                key = f"[{i}]"
                is_primitive_list = isinstance(value, list) and not any(isinstance(i, (dict, list)) for i in value)

                if is_primitive_list:
                    child_item = TreeItem(key, value, parent)
                    parent.appendChild(child_item)
                elif isinstance(value, (dict, list)):
                    child_item = TreeItem(key, None, parent)
                    parent.appendChild(child_item)
                    self._setup_model_data(value, child_item, depth + 1)
                else:
                    child_item = TreeItem(key, value, parent)
                    parent.appendChild(child_item)

    def data(self, index, role):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        item = index.internalPointer()
        return item.data(index.column())

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._root_item.data(section)
        return None

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self._root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.childCount()

    def columnCount(self, parent=QModelIndex()):
        return self._root_item.columnCount()