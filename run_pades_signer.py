import sys
import os
from PyQt5.QtWidgets import QApplication

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
