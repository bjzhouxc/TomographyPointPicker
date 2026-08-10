from typing import Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class PointListItem(QWidget):
    def __init__(self, index: int, x: int, y: int, color: Tuple[int, int, int], size: int,
                 delete_callback, source: str = "top", parent=None):
        """
        Args:
            source: "top" 或 "bottom"
        """
        super().__init__(parent)
        self.index = index
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.source = source
        self.delete_callback = delete_callback
        self.double_click_callback = None  # 新增：双击回调

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            PointListItem {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
            }
            PointListItem:hover {
                background: #f0f8ff;
                border: 1px solid #cce5ff;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # 来源标识
        source_icon = "📷" if source == "top" else "📄"
        self.source_label = QLabel(source_icon)
        self.source_label.setFixedWidth(24)
        self.source_label.setAlignment(Qt.AlignCenter)
        self.source_label.setToolTip("上方图片点" if source == "top" else "下方图片点")
        layout.addWidget(self.source_label)

        # 颜色指示器
        self.color_indicator = QLabel()
        self.color_indicator.setFixedSize(14, 14)
        self.color_indicator.setStyleSheet(f"""
            background: rgb({color[0]}, {color[1]}, {color[2]});
            border: 1px solid #666666;
            border-radius: 3px;
        """)
        self.color_indicator.setToolTip(f"RGB({color[0]}, {color[1]}, {color[2]})")
        layout.addWidget(self.color_indicator)

        # 显示坐标和大小
        self.coord_label = QLabel(f"点 {index + 1}: ({x}, {y}) {size}px")
        self.coord_label.setStyleSheet("color: #333333; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.coord_label, 1)

        # 删除按钮
        self.delete_btn = QPushButton("✕")
        self.delete_btn.setFixedSize(16, 16)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: #ff4444;
                color: white;
                border: none;
                border-radius: 8px;
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
        self.delete_btn.setToolTip("删除此点")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)

    def set_double_click_callback(self, callback):
        """设置双击回调函数"""
        self.double_click_callback = callback

    def mouseDoubleClickEvent(self, event):
        """处理双击事件"""
        if event.button() == Qt.LeftButton:
            if self.double_click_callback:
                self.double_click_callback(self.index, self.x, self.y)
        super().mouseDoubleClickEvent(event)

    def on_delete_clicked(self):
        if self.delete_callback:
            self.delete_callback(self.index)

    def update_index(self, new_index: int):
        """更新索引（当列表重新排序时调用）"""
        self.index = new_index
        self.coord_label.setText(f"点 {new_index + 1}: ({self.x}, {self.y}) {self.size}px")