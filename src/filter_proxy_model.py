from PyQt6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_case_sensitivity = Qt.CaseSensitivity.CaseInsensitive
        self._use_regex = False
        self._filter_value_only = False
        self.setFilterKeyColumn(-1) # Filter all columns by default

    def set_filter_case_sensitivity(self, cs):
        self._filter_case_sensitivity = cs
        self.invalidateFilter()

    def set_use_regex(self, use_regex):
        self._use_regex = use_regex
        self.invalidateFilter()

    def set_filter_value_only(self, value_only):
        # In a DataFrame-centric model, this is less relevant,
        # but we can map it to filtering on a specific column if needed.
        # For now, we'll just invalidate the filter.
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filterRegularExpression().pattern():
            return True

        model = self.sourceModel()
        if not hasattr(model, '_data'):
            return True # Not a PandasModel

        df_row = model._data.iloc[source_row]

        for col in df_row.index:
            if self.filterRegularExpression().search(str(df_row[col])).hasMatch():
                return True
        return False

    def setFilterRegularExpression(self, pattern):
        options = QRegularExpression.PatternOption.NoPatternOption
        if self._filter_case_sensitivity == Qt.CaseSensitivity.CaseInsensitive:
            options |= QRegularExpression.PatternOption.CaseInsensitiveOption

        if not self._use_regex:
            pattern = QRegularExpression.escape(pattern)

        regex = QRegularExpression(pattern, options)
        super().setFilterRegularExpression(regex)