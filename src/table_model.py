from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QFont
import pandas as pd
import numpy as np


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                if pd.isna(value):
                    return ""  # Display NaN as empty string
                return str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

        if role == Qt.ItemDataRole.FontRole and orientation == Qt.Orientation.Horizontal:
            font = QFont()
            font.setBold(True)
            return font

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role == Qt.ItemDataRole.EditRole:
            col = index.column()
            row = index.row()
            original_dtype = self._data.dtypes[col]

            # Handle empty input gracefully
            if value == '':
                if pd.api.types.is_numeric_dtype(original_dtype):
                    self._data.iloc[row, col] = np.nan
                    self.dataChanged.emit(index, index)
                    return True
                # For non-numeric types, an empty string might be valid

            # Try to cast the new value to the original type
            try:
                # Use pandas to handle the conversion, which is robust
                casted_value = pd.Series([value]).astype(original_dtype).iloc[0]
                self._data.iloc[row, col] = casted_value
                self.dataChanged.emit(index, index)
                return True
            except (ValueError, TypeError):
                # If casting fails (e.g., "abc" to int), reject the edit
                return False
        return False

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def insertRows(self, row, count, parent=None):
        self.beginInsertRows(parent or self.createIndex(0, 0), row, row + count - 1)

        # Create a new DataFrame for the new rows, filled with NaNs or default values
        new_rows = pd.DataFrame(
            np.nan,
            index=range(count),
            columns=self._data.columns
        )

        # Split the original DataFrame and insert the new rows
        df_top = self._data.iloc[:row]
        df_bottom = self._data.iloc[row:]
        self._data = pd.concat([df_top, new_rows, df_bottom]).reset_index(drop=True)

        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=None):
        self.beginRemoveRows(parent or self.createIndex(0, 0), row, row + count - 1)

        # Drop the specified rows
        self._data.drop(self._data.index[row:row+count], inplace=True)
        self._data.reset_index(drop=True, inplace=True)

        self.endRemoveRows()
        return True
