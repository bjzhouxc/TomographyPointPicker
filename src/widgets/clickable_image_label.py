from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy


class ClickableImageLabel(QLabel):
    """可点击/可拖动的图片标签"""

    def __init__(self, click_handler, drag_handler=None, parent=None):
        super().__init__(parent)
        self.click_handler = click_handler
        self.drag_handler = drag_handler
        self.is_dragging = False
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setFrameShape(QFrame.Panel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(2)
        self.setStyleSheet("background: white;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)  # 启用鼠标追踪

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.click_handler(event.position().x(), event.position().y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.drag_handler is not None:
            self.drag_handler(event.position().x(), event.position().y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
        super().mouseReleaseEvent(event)