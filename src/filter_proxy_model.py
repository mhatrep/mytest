from PyQt6.QtCore import QSortFilterProxyModel, Qt, QRegularExpression

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_case_sensitivity = Qt.CaseSensitivity.CaseInsensitive
        self._use_regex = False
        self._filter_value_only = False

    def set_filter_case_sensitivity(self, cs):
        self._filter_case_sensitivity = cs
        self.invalidateFilter()

    def set_use_regex(self, use_regex):
        self._use_regex = use_regex
        self.invalidateFilter()

    def set_filter_value_only(self, value_only):
        self._filter_value_only = value_only
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filterRegularExpression().pattern():
            return True

        source_model = self.sourceModel()

        if self._filter_value_only:
            # Column 3 is the "Value" column
            index = source_model.index(source_row, 3, source_parent)
            data = str(source_model.data(index, Qt.ItemDataRole.DisplayRole))
            return self.evaluate_filter(data)
        else:
            for i in range(source_model.columnCount(source_parent)):
                index = source_model.index(source_row, i, source_parent)
                data = str(source_model.data(index, Qt.ItemDataRole.DisplayRole))
                if self.evaluate_filter(data):
                    return True
            return False

    def evaluate_filter(self, data):
        regex = self.filterRegularExpression()
        if self._use_regex:
            return regex.match(data).hasMatch()
        else:
            # Simple substring search
            pattern = self.filterRegularExpression().pattern()
            if self.filterCaseSensitivity() == Qt.CaseSensitivity.CaseInsensitive:
                return pattern.lower() in data.lower()
            else:
                return pattern in data

    def setFilterRegularExpression(self, pattern):
        options = QRegularExpression.PatternOption.NoPatternOption
        if self._filter_case_sensitivity == Qt.CaseSensitivity.CaseInsensitive:
            options |= QRegularExpression.PatternOption.CaseInsensitiveOption

        if not self._use_regex:
            pattern = QRegularExpression.escape(pattern)

        regex = QRegularExpression(pattern, options)
        super().setFilterRegularExpression(regex)