from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy


class ClickableImageLabel(QLabel):
    """可点击的图片标签"""

    def __init__(self, click_handler, parent=None):
        super().__init__(parent)
        self.click_handler = click_handler
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(2)
        self.setStyleSheet("background: white;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_handler(event.position().x(), event.position().y())
        super().mousePressEvent(event)