import sys
from PySide6.QtWidgets import QApplication
from .viewer import ImageViewerApp


def main():
    app = QApplication(sys.argv)
    viewer = ImageViewerApp()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()