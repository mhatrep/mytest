from PyQt6.QtCore import QSortFilterProxyModel, Qt

class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._filter_text = ""
        self._case_sensitive = False

    def set_filter_text(self, text):
        self._filter_text = text
        self.invalidateFilter()

    def set_case_sensitive(self, case_sensitive):
        self._case_sensitive = case_sensitive
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self._filter_text:
            return True

        index0 = self.sourceModel().index(source_row, 0, source_parent)
        index1 = self.sourceModel().index(source_row, 1, source_parent)

        text0 = self.sourceModel().data(index0, Qt.ItemDataRole.DisplayRole)
        text1 = self.sourceModel().data(index1, Qt.ItemDataRole.DisplayRole)

        if text0 is None:
            text0 = ""
        if text1 is None:
            text1 = ""

        haystack = f"{text0}{text1}"
        needle = self._filter_text

        if not self._case_sensitive:
            haystack = haystack.lower()
            needle = needle.lower()

        if needle in haystack:
            return True

        # Check if any child of the current row matches
        if self.sourceModel().hasChildren(index0):
            for i in range(self.sourceModel().rowCount(index0)):
                if self.filterAcceptsRow(i, index0):
                    return True

        return False