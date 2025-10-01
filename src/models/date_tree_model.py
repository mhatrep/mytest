from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import QDate, Qt
import calendar

class DateTreeModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(["Date"])
        self.populate_tree()

    def populate_tree(self):
        today = QDate.currentDate()
        current_year = today.year()
        current_month = today.month()

        self.add_year(current_year, current_month)

    def add_year(self, year, current_month):
        year_item = QStandardItem(str(year))
        year_item.setEditable(False)
        self.appendRow(year_item)

        for month in range(1, 13):
            month_name = calendar.month_name[month]
            month_item = QStandardItem(f"{month:02d} - {month_name}")
            month_item.setEditable(False)
            month_item.setData((year, month), Qt.ItemDataRole.UserRole)
            year_item.appendRow(month_item)

            if month == current_month:
                self.add_days(month_item, year, month)

    def add_days(self, month_item, year, month):
        _, num_days = calendar.monthrange(year, month)
        for day in range(1, num_days + 1):
            day_item = QStandardItem(f"{day:02d}")
            day_item.setEditable(False)
            day_item.setData(QDate(year, month, day), Qt.ItemDataRole.UserRole)
            month_item.appendRow(day_item)