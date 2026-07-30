from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

class PointListItem(QWidget):
    """点列表项组件"""

    def __init__(self, index: int, x: int, y: int, delete_callback, parent=None):
        super().__init__(parent)
        self.index = index
        self.x = x
        self.y = y
        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # 显示坐标
        self.coord_label = QLabel(f"点 {index + 1}: ({x}, {y})")
        self.coord_label.setStyleSheet("color: #333333; font-size: 12px;")
        layout.addWidget(self.coord_label, 1)

        # 删除按钮
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(12, 12)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #ff4444;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #cc0000;
            }
            QPushButton:pressed {
                background: #990000;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)

    def on_delete_clicked(self):
        """删除按钮点击事件"""
        if self.delete_callback:
            self.delete_callback(self.index)