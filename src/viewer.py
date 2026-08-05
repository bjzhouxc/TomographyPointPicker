import os

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QColorDialog,
)

from .widgets import PathLineEdit, ClickableImageLabel, PointListItem
from .controllers import ImageController
from .utils import ImageUtils


class ImageViewerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tomography Point Picker")
        self.resize(1025, 1000)

        # 定义尺寸常量
        self.top_size = 512
        self.bottom_width = 512
        self.bottom_height = 1920
        self.display_size = 512

        # 存储图片对象
        self.top_photo = None
        self.bottom_photo = None
        self.bottom_display_photo = None
        self.top_line_photo = None
        self.bottom_line_photo = None
        self.bottom_line_image = None

        # 初始化控制器
        self.controller = ImageController(self)

        # 当前选中的点颜色（默认红色）
        self.point_color = (0, 255, 0)

        self.setup_ui()
        self.show_placeholders()

    def setup_ui(self):
        """创建界面组件"""
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # ----- 左侧控制区域 -----
        left_panel = QWidget(self)
        left_panel.setFixedWidth(450)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(8)
        root_layout.addWidget(left_panel)

        # 第一行：上方图片输入
        row1_layout = QHBoxLayout()
        left_layout.addLayout(row1_layout)

        label1 = QLabel("上方图片路径:")
        row1_layout.addWidget(label1)

        self.url_entry_top = PathLineEdit(self.select_top_image)
        self.url_entry_top.setPlaceholderText("双击选择上方图片路径")
        row1_layout.addWidget(self.url_entry_top, 1)

        load_btn1 = QPushButton("加载上方图片")
        load_btn1.setStyleSheet("background: #4CAF50; color: white; padding: 4px 10px;")
        load_btn1.clicked.connect(self.select_top_image)
        row1_layout.addWidget(load_btn1)

        # 第二行：下方图片输入
        row2_layout = QHBoxLayout()
        left_layout.addLayout(row2_layout)

        label2 = QLabel("数据文件夹路径:")
        row2_layout.addWidget(label2)

        self.url_entry_bottom = PathLineEdit(self.select_data_folder)
        self.url_entry_bottom.setPlaceholderText("双击选择数据文件夹路径")
        row2_layout.addWidget(self.url_entry_bottom, 1)

        load_btn2 = QPushButton("加载数据图片")
        load_btn2.setStyleSheet("background: #2196F3; color: white; padding: 4px 10px;")
        load_btn2.clicked.connect(self.select_data_folder)
        row2_layout.addWidget(load_btn2)

        # 信息标签
        self.info_label = QLabel("B-scan: 未加载")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("background: #F0F0F0; color: #666666;")
        left_layout.addWidget(self.info_label)

        # 透明度控制
        opacity_layout = QHBoxLayout()
        left_layout.addLayout(opacity_layout)

        opacity_label = QLabel("覆盖透明度:")
        opacity_layout.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(0)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)

        self.opacity_value_label = QLabel("0%")
        self.opacity_value_label.setFixedWidth(40)
        opacity_layout.addWidget(self.opacity_value_label)

        # ---- 侧面图压缩控制 ----
        compress_layout = QHBoxLayout()
        left_layout.addLayout(compress_layout)

        compress_label = QLabel("侧面图压缩:")
        compress_layout.addWidget(compress_label)

        self.compress_slider = QSlider(Qt.Horizontal)
        self.compress_slider.setRange(1, 100)  # 1% - 100%
        self.compress_slider.setValue(100)
        self.compress_slider.valueChanged.connect(self.on_compress_changed)
        compress_layout.addWidget(self.compress_slider)

        self.compress_value_label = QLabel("100%")
        self.compress_value_label.setFixedWidth(40)
        compress_layout.addWidget(self.compress_value_label)

        # ---- 对比度控制 ----
        # 上方图片对比度
        contrast_top_layout = QHBoxLayout()
        left_layout.addLayout(contrast_top_layout)

        contrast_top_label = QLabel("上方对比度:")
        contrast_top_layout.addWidget(contrast_top_label)

        self.contrast_top_slider = QSlider(Qt.Horizontal)
        self.contrast_top_slider.setRange(0, 200)  # 0% - 200%
        self.contrast_top_slider.setValue(100)  # 默认100%
        self.contrast_top_slider.valueChanged.connect(self.on_contrast_top_changed)
        contrast_top_layout.addWidget(self.contrast_top_slider)

        self.contrast_top_value_label = QLabel("100%")
        self.contrast_top_value_label.setFixedWidth(40)
        contrast_top_layout.addWidget(self.contrast_top_value_label)

        # 下方图片对比度
        contrast_bottom_layout = QHBoxLayout()
        left_layout.addLayout(contrast_bottom_layout)

        contrast_bottom_label = QLabel("下方对比度:")
        contrast_bottom_layout.addWidget(contrast_bottom_label)

        self.contrast_bottom_slider = QSlider(Qt.Horizontal)
        self.contrast_bottom_slider.setRange(0, 200)
        self.contrast_bottom_slider.setValue(100)
        self.contrast_bottom_slider.valueChanged.connect(self.on_contrast_bottom_changed)
        contrast_bottom_layout.addWidget(self.contrast_bottom_slider)

        self.contrast_bottom_value_label = QLabel("100%")
        self.contrast_bottom_value_label.setFixedWidth(40)
        contrast_bottom_layout.addWidget(self.contrast_bottom_value_label)

        # ---- 点管理区域 ----
        self.setup_point_management(left_layout)

        # 绑定回车键
        self.url_entry_top.returnPressed.connect(lambda: self.load_image("top_only"))
        self.url_entry_bottom.returnPressed.connect(lambda: self.load_image("both"))

        left_layout.addStretch()

        # ----- 右侧图片显示区域 -----
        self.setup_image_display(root_layout)

    def setup_point_management(self, parent_layout):
        """设置点管理区域"""
        point_group = QGroupBox("标注点管理")
        point_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        point_layout = QVBoxLayout(point_group)

        # ---- 点大小控制 ----
        size_layout = QHBoxLayout()

        size_label = QLabel("点大小:")
        size_layout.addWidget(size_label)

        self.point_size_slider = QSlider(Qt.Horizontal)
        self.point_size_slider.setRange(1, 20)  # 1-20像素
        self.point_size_slider.setValue(5)  # 默认5
        self.point_size_slider.valueChanged.connect(self.on_point_size_changed)
        size_layout.addWidget(self.point_size_slider)

        self.point_size_label = QLabel("5px")
        self.point_size_label.setFixedWidth(40)
        size_layout.addWidget(self.point_size_label)

        point_layout.addLayout(size_layout)

        # ---- 按钮行（颜色选择 + 记录 + 清空） ----
        button_layout = QHBoxLayout()

        # 颜色选择按钮
        self.color_picker_btn = QPushButton("🎨")
        self.color_picker_btn.setFixedSize(32, 32)
        self.color_picker_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgb({self.point_color[0]}, {self.point_color[1]}, {self.point_color[2]});
                border-radius: 4px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border: 2px solid #666666;
            }}
        """)
        self.color_picker_btn.setToolTip("选择点的颜色")
        self.color_picker_btn.clicked.connect(self.choose_point_color)
        button_layout.addWidget(self.color_picker_btn)

        # 记录点按钮
        self.record_point_btn = QPushButton("📌 记录该点")
        self.record_point_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.record_point_btn.clicked.connect(self.record_current_point)
        self.record_point_btn.setEnabled(False)
        button_layout.addWidget(self.record_point_btn)

        # 清空所有点按钮
        self.clear_points_btn = QPushButton("🗑 清空所有")
        self.clear_points_btn.setStyleSheet("""
            QPushButton {
                background: #ff6b6b;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff5252;
            }
            QPushButton:pressed {
                background: #e04848;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.clear_points_btn.clicked.connect(self.clear_all_points)
        self.clear_points_btn.setEnabled(False)
        button_layout.addWidget(self.clear_points_btn)

        point_layout.addLayout(button_layout)

        # 点列表
        list_label = QLabel("已记录的点:")
        list_label.setStyleSheet("font-weight: bold; color: #555555; margin-top: 5px;")
        point_layout.addWidget(list_label)

        self.point_list_widget = QListWidget()
        self.point_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
                min-height: 150px;
                max-height: 200px;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
            }
        """)
        self.point_list_widget.setSpacing(1)
        point_layout.addWidget(self.point_list_widget)

        self.point_count_label = QLabel("总计: 0 个点")
        self.point_count_label.setStyleSheet("color: #666666; font-size: 11px;")
        point_layout.addWidget(self.point_count_label)

        parent_layout.addWidget(point_group)

    def setup_image_display(self, root_layout):
        """设置图片显示区域"""
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        root_layout.addWidget(right_panel, 1)

        # 上方图片显示
        top_frame = QGroupBox("上方图片 - 点击选择坐标")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(5, 5, 5, 5)

        self.top_image_label = ClickableImageLabel(self.on_top_image_click)
        self.top_image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        top_layout.addWidget(self.top_image_label)
        right_layout.addWidget(top_frame, 1)

        # 下方图片显示 - 改为 ClickableImageLabel
        bottom_frame = QGroupBox("下方图片 - 点击更新X坐标")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(5, 5, 5, 5)

        self.bottom_scroll_area = QScrollArea()
        self.bottom_scroll_area.setWidgetResizable(False)
        self.bottom_scroll_area.setFrameShape(QFrame.Panel)
        self.bottom_scroll_area.setFrameShadow(QFrame.Sunken)
        self.bottom_scroll_area.setLineWidth(2)
        self.bottom_scroll_area.setStyleSheet("background: white;")

        # 改为 ClickableImageLabel
        self.bottom_image_label = ClickableImageLabel(self.on_bottom_image_click)
        self.bottom_image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.bottom_image_label.setStyleSheet("background: white;")
        self.bottom_scroll_area.setWidget(self.bottom_image_label)

        bottom_layout.addWidget(self.bottom_scroll_area)
        right_layout.addWidget(bottom_frame, 1)
    # ========== 颜色选择功能 ==========

    def choose_point_color(self):
        """打开颜色选择对话框"""
        current_color = QColor(self.point_color[0], self.point_color[1], self.point_color[2])
        color = QColorDialog.getColor(current_color, self, "选择点的颜色")

        if color.isValid():
            self.point_color = (color.red(), color.green(), color.blue())
            # 更新颜色按钮的样式
            self.color_picker_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgb({self.point_color[0]}, {self.point_color[1]}, {self.point_color[2]});
                    border-radius: 4px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    border: 2px solid #666666;
                }}
            """)
            # 如果有点已经记录，不自动重新绘制，等待用户操作

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.controller.current_x is not None:
            self.draw_bottom_line(self.controller.current_x)
        else:
            self.update_bottom_display()

    def show_error(self, title, text):
        QMessageBox.critical(self, title, text)

    def show_warning(self, title, text):
        QMessageBox.warning(self, title, text)

    def set_label_image(self, label, image):
        pixmap = ImageUtils.pil_to_pixmap(image)
        label.setPixmap(pixmap)
        label.setMinimumSize(pixmap.size())
        return pixmap

    def show_placeholders(self):
        """显示占位图（无文字）"""
        top_placeholder = Image.new("RGB", (self.top_size, self.top_size), (240, 240, 240))
        self.top_placeholder_photo = self.set_label_image(self.top_image_label, top_placeholder)

        bottom_placeholder = Image.new("RGB", (self.bottom_width, self.bottom_height), (245, 245, 245))
        self.bottom_placeholder_photo = self.set_label_image(self.bottom_image_label, bottom_placeholder)

    def on_top_image_click(self, x, y):
        if self.controller.top_image is None and self.controller.base_image is None:
            return

        # 获取label的实际尺寸
        label_width = self.top_image_label.width()
        label_height = self.top_image_label.height()

        pixmap = self.top_image_label.pixmap()
        if pixmap is None:
            return

        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        if label_width <= 0 or label_height <= 0 or pixmap_width <= 0 or pixmap_height <= 0:
            return

        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        display_width = int(pixmap_width * ratio)
        display_height = int(pixmap_height * ratio)

        offset_x = self.controller.top_offset_x
        offset_y = self.controller.top_offset_y

        img_x = x - offset_x
        img_y = y - offset_y

        if img_x < 0 or img_x >= display_width or img_y < 0 or img_y >= display_height:
            return

        if self.controller.base_image is not None:
            orig_width, orig_height = self.controller.base_image.size
        elif self.controller.top_image is not None:
            orig_width, orig_height = self.controller.top_image.size
        else:
            return

        original_x = int((img_x / display_width) * orig_width)
        original_y = int((img_y / display_height) * orig_height)

        original_x = max(1, min(orig_width, original_x))
        original_y = max(1, min(orig_height, original_y))

        self.controller.set_coordinate(original_x, original_y)

        self.draw_crosshair(original_x, original_y)
        self.switch_bottom_image_by_y(original_y)

        self.record_point_btn.setEnabled(True)

    def on_bottom_image_click(self, x, y):
        """下方图片点击事件 - 更新X坐标"""
        if self.controller.bottom_image is None:
            return

        # 获取label的实际尺寸
        label_width = self.bottom_image_label.width()
        label_height = self.bottom_image_label.height()

        # 获取滚动条偏移
        scroll_x = self.bottom_scroll_area.horizontalScrollBar().value()
        scroll_y = self.bottom_scroll_area.verticalScrollBar().value()

        pixmap = self.bottom_image_label.pixmap()
        if pixmap is None:
            return

        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        if label_width <= 0 or label_height <= 0 or pixmap_width <= 0 or pixmap_height <= 0:
            return

        # 计算图片在label中实际显示的大小
        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        display_width = int(pixmap_width * ratio)
        display_height = int(pixmap_height * ratio)

        # 检查是否点击在图片范围内
        if x < 0 or x >= display_width or y < 0 or y >= display_height:
            return

        # 获取原始图片的尺寸
        orig_width, orig_height = self.controller.bottom_image.size

        # 将点击位置映射到原始图片坐标
        original_x = int((x / display_width) * orig_width)
        original_y = int((y / display_height) * orig_height)

        # 确保坐标在有效范围内
        original_x = max(1, min(orig_width, original_x))
        original_y = max(1, min(orig_height, original_y))

        # 更新 current_x（保持current_y不变）
        self.controller.current_x = original_x
        if self.controller.current_y is None:
            self.controller.current_y = 0

        # 更新窗口标题
        self.setWindowTitle(f"Tomography Point Picker - X={original_x}, Y={self.controller.current_y}")

        # 刷新上方图片显示十字准星
        if self.controller.current_y is not None:
            self.draw_crosshair(original_x, self.controller.current_y)

        # 刷新下方图片的绿线
        self.draw_bottom_line(original_x)

        # 启用记录按钮
        self.record_point_btn.setEnabled(True)

    def on_opacity_changed(self, value):
        """透明度滑块变化时的处理"""
        self.controller.set_opacity(value)
        self.opacity_value_label.setText(f"{value}%")
        self.update_top_display()

    def on_compress_changed(self, value):
        """压缩滑块变化时的处理"""
        self.controller.set_compress_ratio(value / 100)
        self.compress_value_label.setText(f"{value}%")
        # 重新加载当前底部图片
        self.switch_bottom_image_by_y(self.controller.current_y)

    def on_point_size_changed(self, value):
        """点大小滑块变化时的处理"""
        self.point_size_label.setText(f"{value}px")
        # 更新 PointManager 中的点大小
        self.controller.get_point_manager().set_point_size(value)
        # 刷新显示
        self.refresh_top_image()

    def on_contrast_top_changed(self, value):
        """上方对比度滑块变化时的处理"""
        self.contrast_top_value_label.setText(f"{value}%")
        self.controller.set_contrast_top(value / 100.0)
        # 刷新上方图片显示
        self.update_top_display()
        self.draw_crosshair(self.controller.current_x, self.controller.current_y)

    def on_contrast_bottom_changed(self, value):
        """下方对比度滑块变化时的处理"""
        self.contrast_bottom_value_label.setText(f"{value}%")
        self.controller.set_contrast_bottom(value / 100.0)
        # 刷新下方图片显示
        self.switch_bottom_image_by_y(self.controller.current_y)

    def draw_crosshair(self, x_coord, y_coord):
        if self.controller.base_image is None and self.controller.top_image is None:
            return

        # 获取干净的图片（从原始图片重新绘制）
        if self.controller.base_image is not None:
            # 有底图，从底图开始
            result_image = self.controller.base_image.copy()
            if self.controller.top_image is not None:
                # 应用透明度
                alpha = self.controller.overlay_opacity / 100.0
                if self.controller.top_image.size != self.controller.base_image.size:
                    overlay_resized = self.controller.top_image.resize(
                        self.controller.base_image.size, Image.Resampling.LANCZOS
                    )
                else:
                    overlay_resized = self.controller.top_image
                # 透明度越高，覆盖图越透明
                overlay_weight = 1.0 - alpha
                result_image = Image.blend(self.controller.base_image, overlay_resized, overlay_weight)
        else:
            # 只有覆盖图
            result_image = self.controller.top_image.copy() if self.controller.top_image is not None else None

        if result_image is None:
            return

        result_image = ImageUtils.adjust_contrast(result_image, self.controller.contrast_top)

        draw = ImageDraw.Draw(result_image)

        # 绘制十字准星
        line_x = x_coord - 1
        draw.line([(line_x, 0), (line_x, self.top_size - 1)], fill=(0, 255, 0), width=2)

        line_y = y_coord - 1
        draw.line([(0, line_y), (self.top_size - 1, line_y)], fill=(255, 0, 0), width=2)

        # 绘制已记录的点（使用当前选中的颜色）
        self.draw_recorded_points(draw)

        self.top_line_photo = self.set_label_image(self.top_image_label, result_image)
        self.draw_bottom_line(x_coord)

    def draw_recorded_points(self, draw):
        """在图片上绘制所有已记录的点"""
        points = self.controller.get_point_manager().get_points()
        if not points:
            return

        for x, y, color, size in points:  # 解包出坐标、颜色、大小
            # 获取图片尺寸
            if self.controller.base_image is not None:
                img_width, img_height = self.controller.base_image.size
            elif self.controller.top_image is not None:
                img_width, img_height = self.controller.top_image.size
            else:
                return

            if 0 <= x < img_width and 0 <= y < img_height:
                radius = size // 2
                draw.ellipse(
                    [(x - radius, y - radius),
                     (x + radius, y + radius)],
                    fill=color
                )

    def draw_bottom_line(self, x_coord):
        if self.controller.bottom_image is None:
            return

        img_copy = self.controller.bottom_image.copy()

        # 确保 x_coord 在图片宽度范围内
        if x_coord >= img_copy.width:
            x_coord = img_copy.width - 1
        if x_coord < 0:
            x_coord = 0

        ImageUtils.draw_vertical_line(img_copy, x_coord)

        self.controller.bottom_line_image = img_copy
        self.update_bottom_display_with_line()

    def update_bottom_display_with_line(self):
        """更新下方图片的显示（包含绿线）"""
        if self.controller.bottom_line_image is None:
            return

        display_image = self.controller.bottom_line_image
        self.bottom_display_photo = self.set_label_image(self.bottom_image_label, display_image)
        self.bottom_line_photo = self.bottom_display_photo

    def switch_bottom_image_by_y(self, y_coord):
        if not y_coord:
            y_coord = 1
        if not self.controller.bottom_image_paths:
            return

        current_scroll_pos = self.bottom_scroll_area.verticalScrollBar().value()

        if self.controller.switch_bottom_image_by_y(y_coord):
            index = y_coord - 1
            total = len(self.controller.bottom_image_paths)
            compress_value = self.compress_slider.value()
            self.info_label.setText(f"图片{index + 1}/{total} (Y={y_coord}) 压缩: {compress_value}%")
            self.info_label.setStyleSheet("background: #F0F0F0; color: #2196F3;")

            if self.controller.current_x is not None:
                img_copy = self.controller.bottom_image.copy()
                ImageUtils.draw_vertical_line(img_copy, self.controller.current_x)
                self.controller.bottom_line_image = img_copy
                self.update_bottom_display_with_line()
            else:
                self.controller.bottom_line_image = None
                self.update_bottom_display()

            # 恢复滚动位置
            self.bottom_scroll_area.verticalScrollBar().setValue(current_scroll_pos)

    def update_top_display(self):
        """更新上方图片显示（合并底座和覆盖图）"""
        # 如果没有底座图片，只显示覆盖图或占位图
        if self.controller.base_image is None:
            if self.controller.top_image is not None:
                # 调整对比度
                result_image = self.controller.top_image.copy()
                result_image = ImageUtils.adjust_contrast(result_image, self.controller.contrast_top)
                self.top_photo = self.set_label_image(self.top_image_label, result_image)
            else:
                self.show_placeholders()
            return

        # 有底图，进行合成
        result_image = self.controller.base_image.copy()

        if self.controller.top_image is not None:
            alpha = self.controller.overlay_opacity / 100.0

            if self.controller.top_image.size != self.controller.base_image.size:
                overlay_resized = self.controller.top_image.resize(
                    self.controller.base_image.size, Image.Resampling.LANCZOS
                )
            else:
                overlay_resized = self.controller.top_image

            # 透明度越高，覆盖图越透明
            overlay_weight = 1.0 - alpha
            result_image = Image.blend(self.controller.base_image, overlay_resized, overlay_weight)

        # 如果有坐标，绘制十字准星
        if self.controller.current_x is not None and self.controller.current_y is not None:
            draw = ImageDraw.Draw(result_image)
            # 绘制十字准星
            line_x = self.controller.current_x - 1
            draw.line([(line_x, 0), (line_x, self.top_size - 1)], fill=(0, 255, 0), width=2)
            line_y = self.controller.current_y - 1
            draw.line([(0, line_y), (self.top_size - 1, line_y)], fill=(255, 0, 0), width=2)
            # 绘制已记录的点
            self.draw_recorded_points(draw)

        result_image = ImageUtils.adjust_contrast(result_image, self.controller.contrast_top)
        # 显示图片
        self.top_photo = self.set_label_image(self.top_image_label, result_image)

    def update_bottom_display(self):
        """更新下方图片的显示"""
        if self.controller.bottom_image is None:
            return

        display_image = self.controller.bottom_image
        self.bottom_display_photo = self.set_label_image(self.bottom_image_label, display_image)

    # ========== 文件加载方法 ==========

    def select_top_image(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择上方图片",
            self.url_entry_top.text().strip() or "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;所有文件 (*)",
        )
        if image_path:
            self.url_entry_top.setText(image_path)
            self.load_image("top_only")

    def select_data_folder(self):
        base_path = QFileDialog.getExistingDirectory(
            self,
            "选择数据文件夹",
            self.url_entry_bottom.text().strip() or "",
        )
        if base_path:
            self.url_entry_bottom.setText(base_path)
            self.load_image("both")

    def load_image(self, mode):
        if mode == "top_only":
            image_path = self.url_entry_top.text().strip()
            if not image_path:
                self.show_warning("提示", "请输入图片路径！")
                return
            if not os.path.exists(image_path):
                self.show_error("错误", f"找不到图片文件：\n{image_path}")
                return

            if self.controller.load_top_image(image_path):
                # 应用当前对比度设置
                contrast_value = self.contrast_top_slider.value() / 100.0
                self.controller.set_contrast_top(contrast_value)
                self.update_top_display()
                if self.controller.current_x is not None and self.controller.current_y is not None:
                    self.draw_crosshair(self.controller.current_x, self.controller.current_y)

        elif mode == "both":
            base_path = self.url_entry_bottom.text().strip()
            if not base_path:
                self.show_warning("提示", "请输入数据文件夹路径！")
                return
            if not os.path.exists(base_path):
                self.show_error("错误", f"找不到路径：\n{base_path}")
                return

            if self.controller.load_data_folder(base_path):
                # 应用当前对比度设置
                contrast_top = self.contrast_top_slider.value() / 100.0
                contrast_bottom = self.contrast_bottom_slider.value() / 100.0
                self.controller.set_contrast_top(contrast_top)
                self.controller.set_contrast_bottom(contrast_bottom)

                compress_value = self.compress_slider.value() / 100.0
                self.controller.set_compress_ratio(compress_value)
                self.update_top_display()

                if self.controller.current_y is not None:
                    self.switch_bottom_image_by_y(self.controller.current_y)
                else:
                    self.switch_bottom_image_by_y(1)
                    self.bottom_scroll_area.verticalScrollBar().setValue(0)

                if self.controller.current_x is not None and self.controller.current_y is not None:
                    self.draw_crosshair(self.controller.current_x, self.controller.current_y)
                    self.record_point_btn.setEnabled(True)

    # ========== 点管理功能 ==========

    def record_current_point(self):
        """记录当前十字准星位置的点"""
        x, y = self.controller.get_coordinate()
        if x is None or y is None:
            self.show_warning("提示", "请先在上方图片中点击选择一个位置")
            return

        # 获取当前选中的大小
        current_size = self.point_size_slider.value()

        # 传入颜色和大小
        if self.controller.get_point_manager().add_point(x, y, self.point_color, current_size):
            self.update_point_list()
            self.refresh_top_image()
            self.show_status_message(f"已记录点 ({x}, {y}) 颜色: RGB{self.point_color} 大小: {current_size}px")
        else:
            self.show_warning("提示", f"点 ({x}, {y}) 已存在")

    def delete_point(self, index):
        """删除指定索引的点"""
        if self.controller.get_point_manager().remove_point(index):
            self.update_point_list()
            self.refresh_top_image()
            self.show_status_message(f"已删除点 {index + 1}")

    def clear_all_points(self):
        """清空所有点"""
        if self.controller.get_point_manager().get_point_count() == 0:
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要删除所有已记录的点吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.controller.get_point_manager().clear_points()
            self.update_point_list()
            self.refresh_top_image()
            self.show_status_message("已清空所有点")

    def update_point_list(self):
        self.point_list_widget.clear()

        points = self.controller.get_point_manager().get_points()

        for i, (x, y, color, size) in enumerate(points):  # 解包出大小
            item = QListWidgetItem(self.point_list_widget)
            item_widget = PointListItem(i, x, y, color, size, self.delete_point)
            item.setSizeHint(item_widget.sizeHint())
            self.point_list_widget.addItem(item)
            self.point_list_widget.setItemWidget(item, item_widget)

        count = len(points)
        self.point_count_label.setText(f"总计: {count} 个点")
        self.clear_points_btn.setEnabled(count > 0)

        if count > 0:
            self.point_list_widget.setStyleSheet("""
                QListWidget {
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    background: white;
                    min-height: 150px;
                    max-height: 200px;
                }
                QListWidget::item {
                    padding: 2px;
                    border-bottom: 1px solid #eeeeee;
                }
                QListWidget::item:selected {
                    background: #e3f2fd;
                }
            """)
        else:
            self.point_list_widget.setStyleSheet("""
                QListWidget {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background: white;
                    min-height: 150px;
                    max-height: 200px;
                }
                QListWidget::item {
                    padding: 2px;
                    border-bottom: 1px solid #eeeeee;
                }
                QListWidget::item:selected {
                    background: #e3f2fd;
                }
            """)

    def refresh_top_image(self):
        """刷新上方图片显示（重新绘制所有点）"""
        if self.controller.current_x is not None and self.controller.current_y is not None:
            self.draw_crosshair(self.controller.current_x, self.controller.current_y)
        else:
            self.update_top_display()

    def show_status_message(self, message):
        """在状态栏显示消息"""
        original_style = self.info_label.styleSheet()
        original_text = self.info_label.text()

        self.info_label.setText(f"✓ {message}")
        self.info_label.setStyleSheet("background: #C8E6C9; color: #2E7D32;")

        from PySide6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.restore_info_label(original_style, original_text))

    def restore_info_label(self, style, text):
        """恢复信息标签"""
        self.info_label.setStyleSheet(style)
        self.info_label.setText(text)