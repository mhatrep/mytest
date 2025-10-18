import sys
from PyQt6.QtWidgets import QApplication
from src.main import MainWindow

def test_app_startup(qtbot):
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.isVisible()