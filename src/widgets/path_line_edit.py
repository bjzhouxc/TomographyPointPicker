from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit


class PathLineEdit(QLineEdit):
    """可双击选择路径的输入框"""

    def __init__(self, double_click_handler, parent=None):
        super().__init__(parent)
        self.double_click_handler = double_click_handler
        self.setReadOnly(True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_click_handler()
        super().mouseDoubleClickEvent(event)