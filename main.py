import sys
from PySide6.QtWidgets import QApplication
from src.viewer import ImageViewerApp


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewerApp()
    viewer.show()
    sys.exit(app.exec())
