import glob
import os
import re

from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
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
)


class PathLineEdit(QLineEdit):
    def __init__(self, double_click_handler, parent=None):
        super().__init__(parent)
        self.double_click_handler = double_click_handler
        self.setReadOnly(True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_click_handler()
        super().mouseDoubleClickEvent(event)


class ClickableImageLabel(QLabel):
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

        # 用于存储图片的偏移量（用于坐标计算）
        self.top_offset_x = 0
        self.top_offset_y = 0
        self.top_display_width = 0
        self.top_display_height = 0

        # 存储当前选择的坐标
        self.current_x = None
        self.current_y = None

        # 存储下方图片路径列表
        self.bottom_image_paths = []

        # 存储图片对象
        self.top_photo = None
        self.bottom_photo = None
        self.top_image = None
        self.base_image = None
        self.bottom_image = None
        self.bottom_display_photo = None

        # 存储线条对象
        self.top_line_photo = None
        self.bottom_line_photo = None
        self.bottom_line_image = None

        self.overlay_opacity = 0

        self.setup_ui()

    def setup_ui(self):
        """创建界面组件"""
        root_layout = QHBoxLayout(self)  # 改为水平布局
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        # ----- 左侧控制区域 -----
        left_panel = QWidget(self)
        left_panel.setFixedWidth(450)  # 固定宽度
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

        # 绑定回车键
        self.url_entry_top.returnPressed.connect(lambda: self.load_image("top_only"))
        self.url_entry_bottom.returnPressed.connect(lambda: self.load_image("both"))

        # 左侧底部留白
        left_layout.addStretch()

        # ----- 右侧图片显示区域 -----
        right_panel = QWidget(self)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)
        root_layout.addWidget(right_panel, 1)  # 占据剩余空间

        # 上方图片显示
        top_frame = QGroupBox("上方图片 - 点击选择坐标")
        top_layout = QVBoxLayout(top_frame)
        top_layout.setContentsMargins(5, 5, 5, 5)

        self.top_image_label = ClickableImageLabel(self.on_top_image_click)
        self.top_image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        top_layout.addWidget(self.top_image_label)
        right_layout.addWidget(top_frame, 1)

        # 下方图片显示
        bottom_frame = QGroupBox("下方图片")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(5, 5, 5, 5)

        self.bottom_scroll_area = QScrollArea()
        self.bottom_scroll_area.setWidgetResizable(False)
        self.bottom_scroll_area.setFrameShape(QFrame.Panel)
        self.bottom_scroll_area.setFrameShadow(QFrame.Sunken)
        self.bottom_scroll_area.setLineWidth(2)
        self.bottom_scroll_area.setStyleSheet("background: white;")

        self.bottom_image_label = QLabel()
        self.bottom_image_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.bottom_image_label.setStyleSheet("background: white;")
        self.bottom_scroll_area.setWidget(self.bottom_image_label)

        bottom_layout.addWidget(self.bottom_scroll_area)
        right_layout.addWidget(bottom_frame, 1)

        # 显示占位图
        self.show_placeholders()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_x is not None:
            self.draw_bottom_line(self.current_x)
        else:
            self.update_bottom_display()

    def show_error(self, title, text):
        QMessageBox.critical(self, title, text)

    def show_warning(self, title, text):
        QMessageBox.warning(self, title, text)

    def set_label_image(self, label, image):
        pixmap = self.pil_to_pixmap(image)
        label.setPixmap(pixmap)
        label.setMinimumSize(pixmap.size())
        return pixmap

    def pil_to_pixmap(self, image):
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        data = rgb_image.tobytes("raw", "RGB")
        qimage = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        return QPixmap.fromImage(qimage)

    def show_placeholders(self):
        # 上方占位图
        top_placeholder = Image.new("RGB", (self.top_size, self.top_size), (240, 240, 240))
        draw = ImageDraw.Draw(top_placeholder)
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except Exception:
            font = ImageFont.load_default()

        text = ""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.top_size - text_width) // 2
        y = (self.top_size - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.top_placeholder_photo = self.set_label_image(self.top_image_label, top_placeholder)

        bottom_placeholder = Image.new("RGB", (self.bottom_width, self.bottom_height), (245, 245, 245))
        draw = ImageDraw.Draw(bottom_placeholder)

        text = ""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.top_size - text_width) // 2
        y = (self.top_size - text_height) // 2
        draw.text((x, y), text, fill=(180, 180, 180), font=font)

        self.bottom_placeholder_photo = self.set_label_image(self.bottom_image_label, bottom_placeholder)

    def on_top_image_click(self, x, y):
        if self.top_image is None and self.base_image is None:
            return

        # 获取label的实际尺寸
        label_width = self.top_image_label.width()
        label_height = self.top_image_label.height()

        # 获取当前显示的pixmap
        pixmap = self.top_image_label.pixmap()
        if pixmap is None:
            return

        # 获取pixmap的原始尺寸（这是图片的实际像素尺寸）
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        if label_width <= 0 or label_height <= 0 or pixmap_width <= 0 or pixmap_height <= 0:
            return

        # 计算图片在label中实际显示的大小（保持比例缩放后）
        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        display_width = int(pixmap_width * ratio)
        display_height = int(pixmap_height * ratio)

        # 左对齐，偏移量为0
        offset_x = 0
        offset_y = 0

        # 计算点击在显示图片上的位置
        img_x = x - offset_x
        img_y = y - offset_y

        # 检查是否点击在图片范围内
        if img_x < 0 or img_x >= display_width or img_y < 0 or img_y >= display_height:
            return

        # 获取原始图片的尺寸（用于坐标转换）
        if self.base_image is not None:
            orig_width, orig_height = self.base_image.size
        elif self.top_image is not None:
            orig_width, orig_height = self.top_image.size
        else:
            return

        # 将点击位置映射到原始图片坐标
        original_x = int((img_x / display_width) * orig_width)
        original_y = int((img_y / display_height) * orig_height)

        # 确保坐标在有效范围内
        original_x = max(1, min(orig_width, original_x))
        original_y = max(1, min(orig_height, original_y))

        self.current_x = original_x
        self.current_y = original_y

        self.setWindowTitle(f"Tomography Point Picker - X={original_x}, Y={original_y}")

        self.draw_crosshair(original_x, original_y)
        self.switch_bottom_image_by_y(original_y)

    def on_opacity_changed(self, value):
        """透明度滑块变化时的处理"""
        self.overlay_opacity = value
        self.opacity_value_label.setText(f"{value}%")
        self.update_top_display()

    def draw_crosshair(self, x_coord, y_coord):
        if self.base_image is None and self.top_image is None:
            return

        # 获取当前显示的图片（需要与update_top_display保持一致）
        if self.base_image is not None:
            # 重新合成图片
            result_image = self.base_image.copy()
            if self.top_image is not None and self.overlay_opacity <= 100:
                alpha = self.overlay_opacity / 100.0
                if self.top_image.size != self.base_image.size:
                    overlay_resized = self.top_image.resize(self.base_image.size, Image.Resampling.LANCZOS)
                else:
                    overlay_resized = self.top_image
                result_image = Image.blend(self.base_image, overlay_resized, 1.0 - alpha)
        else:
            result_image = self.top_image.copy() if self.top_image is not None else None

        if result_image is None:
            return

        draw = ImageDraw.Draw(result_image)

        line_x = x_coord - 1
        draw.line([(line_x, 0), (line_x, self.top_size-1)], fill=(0, 255, 0), width=2)

        line_y = y_coord - 1
        draw.line([(0, line_y), (self.top_size-1, line_y)], fill=(255, 0, 0), width=2)

        self.top_line_photo = self.set_label_image(self.top_image_label, result_image)
        self.draw_bottom_line(x_coord)

    def draw_bottom_line(self, x_coord):
        if self.bottom_image is None:
            return

        img_copy = self.bottom_image.copy()
        draw = ImageDraw.Draw(img_copy)

        line_x = x_coord - 1
        draw.line([(line_x, 0), (line_x, self.bottom_height-1)], fill=(0, 255, 0), width=2)

        self.bottom_line_image = img_copy
        self.update_bottom_display_with_line()

    def update_bottom_display_with_line(self):
        """更新下方图片的显示（包含绿线）"""
        if not hasattr(self, "bottom_line_image") or self.bottom_line_image is None:
            return

        display_image = self.bottom_line_image
        self.bottom_display_photo = self.set_label_image(self.bottom_image_label, display_image)
        self.bottom_line_photo = self.bottom_display_photo

    def switch_bottom_image_by_y(self, y_coord):
        if not self.bottom_image_paths:
            return

        index = y_coord - 1

        if index < 0 or index >= len(self.bottom_image_paths):
            return

        # 保存当前滚动位置
        current_scroll_pos = self.bottom_scroll_area.verticalScrollBar().value()

        try:
            image_path = self.bottom_image_paths[index]
            original_image = Image.open(image_path)

            resized_image, _ = self.resize_and_center_with_info(original_image, (self.bottom_width, self.bottom_height))
            self.bottom_image = resized_image

            self.info_label.setText(f"图片{index + 1}/{len(self.bottom_image_paths)} (Y={y_coord})")
            self.info_label.setStyleSheet("background: #F0F0F0; color: #2196F3;")

            # 如果有x坐标，绘制绿线
            if self.current_x is not None:
                img_copy = resized_image.copy()
                draw = ImageDraw.Draw(img_copy)
                line_x = self.current_x - 1
                draw.line([(line_x, 0), (line_x, 1919)], fill=(0, 255, 0), width=2)
                self.bottom_line_image = img_copy
                self.update_bottom_display_with_line()
            else:
                self.bottom_line_image = None
                self.update_bottom_display()

            # 恢复滚动位置（在新的图片加载完成后）
            self.bottom_scroll_area.verticalScrollBar().setValue(current_scroll_pos)

        except Exception as e:
            self.show_error("错误", f"加载图片失败：\n{str(e)}")

    def sort_by_number(self, filename):
        match = re.search(r"_(\d+)\.png$", filename)
        if match:
            return int(match.group(1))
        return 0

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

            try:
                original_image = Image.open(image_path)
                resized_image, display_info = self.resize_and_center_with_info(original_image, (self.top_size, self.top_size))
                # 存储为覆盖图片
                self.top_image = resized_image
                # 更新显示
                self.update_top_display()

                self.top_display_width = display_info["display_width"]
                self.top_display_height = display_info["display_height"]
                self.top_offset_x = display_info["offset_x"]
                self.top_offset_y = display_info["offset_y"]

                self.setWindowTitle("Tomography Point Picker - Angio已加载")

                # 恢复十字准星
                if self.current_x is not None and self.current_y is not None:
                    self.draw_crosshair(self.current_x, self.current_y)

            except Exception as e:
                self.show_error("错误", f"加载图片失败：\n{str(e)}")

        elif mode == "both":
            # 同时加载Angio和B-scan
            base_path = self.url_entry_bottom.text().strip()

            if not base_path:
                self.show_warning("提示", "请输入数据文件夹路径！")
                return

            if not os.path.exists(base_path):
                self.show_error("错误", f"找不到路径：\n{base_path}")
                return

            try:
                # 加载Angio
                angio_path = os.path.join(base_path, "Angio")
                # 在 load_image 方法的 both 分支中，原来加载Angio的部分：
                if os.path.exists(angio_path):
                    png_files = glob.glob(os.path.join(angio_path, "*.png"))
                    if png_files:
                        image_path = png_files[0]
                        original_image = Image.open(image_path)
                        resized_image, display_info = self.resize_and_center_with_info(original_image, (self.top_size, self.top_size))
                        # 存储为底座图片
                        self.base_image = resized_image
                        # 更新显示
                        self.update_top_display()

                        self.top_display_width = display_info["display_width"]
                        self.top_display_height = display_info["display_height"]
                        self.top_offset_x = display_info["offset_x"]
                        self.top_offset_y = display_info["offset_y"]

                # 加载B-scan
                bscan_path = os.path.join(base_path, "B-scan_PixelRatio")
                if not os.path.exists(bscan_path):
                    self.show_error("错误", f"找不到B-scan_PixelRatio文件夹：\n{bscan_path}")
                    return

                png_files = sorted(glob.glob(os.path.join(bscan_path, "*.png")))
                if not png_files:
                    self.show_error("错误", f"B-scan_PixelRatio文件夹中没有png图片：\n{bscan_path}")
                    return

                self.bottom_image_paths = sorted(png_files, key=self.sort_by_number)

                if self.current_y is not None:
                    self.switch_bottom_image_by_y(self.current_y)
                else:
                    self.switch_bottom_image_by_y(1)
                    # 首次加载时置顶
                    self.bottom_scroll_area.verticalScrollBar().setValue(0)

                self.setWindowTitle(f"Tomography Point Picker - Angio + B-scan已加载 ({len(png_files)}张)")

                # 恢复十字准星
                if self.current_x is not None and self.current_y is not None:
                    self.draw_crosshair(self.current_x, self.current_y)

            except Exception as e:
                self.show_error("错误", f"加载失败：\n{str(e)}")

    def update_top_display(self):
        """更新上方图片显示（合并底座和覆盖图）"""
        # 如果没有底座图片，只显示覆盖图或占位图
        if self.base_image is None:
            if self.top_image is not None:
                self.top_photo = self.set_label_image(self.top_image_label, self.top_image)
            else:
                self.show_placeholders()
            return

        # 如果有底座图片，开始合成
        result_image = self.base_image.copy()

        if self.top_image is not None and self.overlay_opacity <= 100:
            # 计算透明度（0-1范围）
            alpha = self.overlay_opacity / 100.0

            # 将覆盖图调整到与底座图相同大小（如果需要）
            if self.top_image.size != self.base_image.size:
                overlay_resized = self.top_image.resize(self.base_image.size, Image.Resampling.LANCZOS)
            else:
                overlay_resized = self.top_image

            # 使用Pillow的blend功能合成
            result_image = Image.blend(self.base_image, overlay_resized, 1.0 - alpha)

        # 显示合成后的图片
        self.top_photo = self.set_label_image(self.top_image_label, result_image)

        if self.current_x is not None and self.current_y is not None:
            self.draw_crosshair(self.current_x, self.current_y)

    def update_bottom_display(self):
        """更新下方图片的显示"""
        if not hasattr(self, "bottom_image") or self.bottom_image is None:
            return

        display_image = self.bottom_image
        self.bottom_display_photo = self.set_label_image(self.bottom_image_label, display_image)

    def resize_and_center_with_info(self, image, target_size):
        """调整图片到目标尺寸并居中（保持比例）"""
        target_width, target_height = target_size

        resized_image = Image.new("RGB", (target_width, target_height), (255, 255, 255))

        width, height = image.size
        ratio = min(target_width / width, target_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        scaled_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        resized_image.paste(scaled_image, (x, y))

        display_info = {
            "display_width": new_width,
            "display_height": new_height,
            "offset_x": x,
            "offset_y": y,
        }

        return resized_image, display_info
