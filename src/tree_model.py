from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

class TreeItem:
    def __init__(self, key, value, parent=None, depth=0, source="", array_level=0):
        self._parent = parent
        self._key = key
        self._value = value
        self._children = []
        self._type = type(value).__name__
        self._depth = depth
        self._source = source
        self._array_level = array_level

    def appendChild(self, item):
        self._children.append(item)

    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def columnCount(self):
        return 7  # Key, Path, Type, Value, Depth, Array Level, Source

    def data(self, column):
        if column == 0:
            return self._key
        elif column == 1:
            return self.path()
        elif column == 2:
            return self._type
        elif column == 3:
            return "" if isinstance(self._value, (dict, list)) else self._value
        elif column == 4:
            return self._depth
        elif column == 5:
            return self._array_level
        elif column == 6:
            return self._source
        return None

    def parent(self):
        return self._parent

    def row(self):
        if self._parent:
            return self._parent._children.index(self)
        return 0

    def path(self):
        path = []
        current = self
        while current and current.parent():
            if isinstance(current.parent()._value, list):
                path.insert(0, f"[{current.row()}]")
            else:
                path.insert(0, str(current._key))
            current = current.parent()
        return ".".join(path).replace(".[", "[")


import os

class TreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None, settings=None, source=""):
        super().__init__(parent)
        self.settings = settings if settings else {}
        self.source = os.path.basename(source) if source else ""
        self._root_item = TreeItem("root", data)
        self._headers = ["Key", "Path", "Type", "Value", "Depth", "Array Level", "Source"]
        self._setup_model_data(data, self._root_item)

    def _setup_model_data(self, data, parent, depth=0, array_level=0):
        if isinstance(data, dict):
            for key, value in data.items():
                item = TreeItem(key, value, parent, depth, self.source, array_level)
                parent.appendChild(item)
                self._setup_model_data(value, item, depth + 1, array_level)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = TreeItem(f"[{i}]", value, parent, depth, self.source, array_level + 1)
                parent.appendChild(item)
                self._setup_model_data(value, item, depth + 1, array_level + 1)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        item = index.internalPointer()
        value = item.data(index.column())

        # Apply formatting from settings
        if index.column() == 3: # Value column
            if value is None:
                return self.settings.get("null_format", "NULL")
            if isinstance(value, bool):
                bool_format = self.settings.get("bool_format", "True/False")
                if bool_format == "true/false":
                    return "true" if value else "false"
                elif bool_format == "1/0":
                    return "1" if value else "0"
                else: # True/False
                    return "True" if value else "False"

            # Truncate long strings
            max_width = self.settings.get("max_cell_width", 100)
            str_value = str(value)
            if len(str_value) > max_width:
                return str_value[:max_width] + "..."

        return value

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def index(self, row, column, parent):
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

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.childCount()

    def columnCount(self, parent):
        return self._root_item.columnCount()