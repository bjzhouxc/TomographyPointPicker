from typing import Tuple
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

class PointListItem(QWidget):
    def __init__(self, index: int, x: int, y: int, color: Tuple[int, int, int], size: int, delete_callback,
                 parent=None):
        super().__init__(parent)
        self.index = index
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.delete_callback = delete_callback

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)

        # 颜色指示器
        self.color_indicator = QLabel()
        self.color_indicator.setFixedSize(12, 12)
        self.color_indicator.setStyleSheet(f"""
            background: rgb({color[0]}, {color[1]}, {color[2]});
            border: 1px solid #999999;
            border-radius: 3px;
        """)
        layout.addWidget(self.color_indicator)

        # 显示坐标和大小
        self.coord_label = QLabel(f"点 {index + 1}: ({x}, {y}) {size}px")
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
                border-radius: 6px;
                font-size: 10px;
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
        if self.delete_callback:
            self.delete_callback(self.index)