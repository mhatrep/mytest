import sys
from PySide6.QtWidgets import QApplication
from pivot_gui import PivotTableApp

def main():
    app = QApplication(sys.argv)
    window = PivotTableApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()