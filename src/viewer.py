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

        # 当前选中的点颜色
        self.point_color = (0, 255, 0)
        self.bottom_point_color = (0, 100, 255)

        # 图层列表相关
        self.layer_list_widget = None
        self.clear_layers_btn = None
        self.remove_layer_btn = None
        self.move_up_btn = None
        self.move_down_btn = None
        self.load_img_btn = None

        # 导出按钮引用
        self.export_log_btn = None
        self.export_json_btn = None
        self.export_info_label = None

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

        # ---- 侧面图压缩控制 ----
        compress_layout = QHBoxLayout()
        left_layout.addLayout(compress_layout)

        compress_label = QLabel("侧面图压缩:")
        compress_layout.addWidget(compress_label)

        self.compress_slider = QSlider(Qt.Horizontal)
        self.compress_slider.setRange(1, 100)
        self.compress_slider.setValue(100)
        self.compress_slider.valueChanged.connect(self.on_compress_changed)
        compress_layout.addWidget(self.compress_slider)

        self.compress_value_label = QLabel("100%")
        self.compress_value_label.setFixedWidth(40)
        compress_layout.addWidget(self.compress_value_label)

        # ---- 对比度控制 ----
        contrast_top_layout = QHBoxLayout()
        left_layout.addLayout(contrast_top_layout)

        contrast_top_label = QLabel("上方对比度:")
        contrast_top_layout.addWidget(contrast_top_label)

        self.contrast_top_slider = QSlider(Qt.Horizontal)
        self.contrast_top_slider.setRange(0, 200)
        self.contrast_top_slider.setValue(100)
        self.contrast_top_slider.valueChanged.connect(self.on_contrast_top_changed)
        contrast_top_layout.addWidget(self.contrast_top_slider)

        self.contrast_top_value_label = QLabel("100%")
        self.contrast_top_value_label.setFixedWidth(40)
        contrast_top_layout.addWidget(self.contrast_top_value_label)

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

        # ---- 上方点管理区域 ----
        self.setup_top_point_management(left_layout)

        # ---- 下方点管理区域 ----
        self.setup_bottom_point_management(left_layout)

        # 绑定回车键
        self.url_entry_bottom.returnPressed.connect(lambda: self.load_image("both"))

        self.setup_export_section(left_layout)

        left_layout.addStretch()

        # ----- 右侧图片显示区域 -----
        self.setup_image_display(root_layout)

    def setup_top_point_management(self, parent_layout):
        """设置上方图片点管理区域 - 包含图层管理"""
        point_group = QGroupBox("📷 上方图片管理")
        point_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2E7D32;
            }
        """)
        point_layout = QVBoxLayout(point_group)

        # ---- 加载图片按钮 ----
        load_layout = QHBoxLayout()

        load_img_btn = QPushButton("📁 加载上方图片")
        load_img_btn.setStyleSheet("""
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
        """)
        load_img_btn.clicked.connect(self.load_additional_top_image)
        load_layout.addWidget(load_img_btn)

        clear_layers_btn = QPushButton("🗑 清空叠加图层")
        clear_layers_btn.setStyleSheet("""
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
        """)
        clear_layers_btn.clicked.connect(self.clear_all_layers)
        load_layout.addWidget(clear_layers_btn)

        point_layout.addLayout(load_layout)

        # ---- 图层列表 ----
        layer_label = QLabel("图层列表 (从上到下):")
        layer_label.setStyleSheet("font-weight: bold; color: #555555; margin-top: 5px;")
        point_layout.addWidget(layer_label)

        self.layer_list_widget = QListWidget()
        self.layer_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
                min-height: 80px;
                max-height: 120px;
            }
            QListWidget::item {
                padding: 0px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
            }
        """)
        self.layer_list_widget.setSpacing(1)
        point_layout.addWidget(self.layer_list_widget)

        # ---- 点大小控制 ----
        size_layout = QHBoxLayout()
        size_label = QLabel("点大小:")
        size_layout.addWidget(size_label)

        self.point_size_slider = QSlider(Qt.Horizontal)
        self.point_size_slider.setRange(1, 20)
        self.point_size_slider.setValue(5)
        self.point_size_slider.valueChanged.connect(self.on_point_size_changed)
        size_layout.addWidget(self.point_size_slider)

        self.point_size_label = QLabel("5px")
        self.point_size_label.setFixedWidth(40)
        size_layout.addWidget(self.point_size_label)

        point_layout.addLayout(size_layout)

        # ---- 按钮行 ----
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
                min-height: 100px;
                max-height: 150px;
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

        # 保存按钮引用
        self.load_img_btn = load_img_btn
        self.clear_layers_btn = clear_layers_btn

    def setup_bottom_point_management(self, parent_layout):
        """设置下方点管理区域"""
        point_group = QGroupBox("📄 下方图片点管理")
        point_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2196F3;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #0D47A1;
            }
        """)
        point_layout = QVBoxLayout(point_group)

        # ---- 点大小控制 ----
        size_layout = QHBoxLayout()

        size_label = QLabel("点大小:")
        size_layout.addWidget(size_label)

        self.bottom_point_size_slider = QSlider(Qt.Horizontal)
        self.bottom_point_size_slider.setRange(1, 20)
        self.bottom_point_size_slider.setValue(5)
        self.bottom_point_size_slider.valueChanged.connect(self.on_bottom_point_size_changed)
        size_layout.addWidget(self.bottom_point_size_slider)

        self.bottom_point_size_label = QLabel("5px")
        self.bottom_point_size_label.setFixedWidth(40)
        size_layout.addWidget(self.bottom_point_size_label)

        point_layout.addLayout(size_layout)

        # ---- 按钮行 ----
        button_layout = QHBoxLayout()

        # 颜色选择按钮
        self.bottom_color_picker_btn = QPushButton("🎨")
        self.bottom_color_picker_btn.setFixedSize(32, 32)
        self.bottom_color_picker_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgb({self.bottom_point_color[0]}, {self.bottom_point_color[1]}, {self.bottom_point_color[2]});
                border-radius: 4px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                border: 2px solid #666666;
            }}
        """)
        self.bottom_color_picker_btn.setToolTip("选择点的颜色")
        self.bottom_color_picker_btn.clicked.connect(self.choose_bottom_point_color)
        button_layout.addWidget(self.bottom_color_picker_btn)

        # 记录点按钮
        self.record_bottom_point_btn = QPushButton("📌 记录该点")
        self.record_bottom_point_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.record_bottom_point_btn.clicked.connect(self.record_bottom_current_point)
        self.record_bottom_point_btn.setEnabled(False)
        button_layout.addWidget(self.record_bottom_point_btn)

        # 清空当前图片点按钮
        self.clear_bottom_points_btn = QPushButton("🗑 清空当前")
        self.clear_bottom_points_btn.setStyleSheet("""
                    QPushButton {
                        background: #d32f2f;
                        color: white;
                        padding: 6px 12px;
                        border: none;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: #c62828;
                    }
                    QPushButton:pressed {
                        background: #b71c1c;
                    }
                    QPushButton:disabled {
                        background: #cccccc;
                        color: #666666;
                    }
                """)
        self.clear_bottom_points_btn.clicked.connect(self.clear_all_bottom_points)
        self.clear_bottom_points_btn.setEnabled(False)
        button_layout.addWidget(self.clear_bottom_points_btn)

        # 清空所有图片点按钮（新增）
        self.clear_all_bottom_points_btn = QPushButton("🗑 清空全部")
        self.clear_all_bottom_points_btn.setStyleSheet("""
            QPushButton {
                background: #d32f2f;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c62828;
            }
            QPushButton:pressed {
                background: #b71c1c;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.clear_all_bottom_points_btn.clicked.connect(self.clear_all_bottom_points_all_images)
        self.clear_all_bottom_points_btn.setEnabled(False)
        button_layout.addWidget(self.clear_all_bottom_points_btn)

        point_layout.addLayout(button_layout)

        # 点列表
        list_label = QLabel("已记录的点 (显示原始坐标):")
        list_label.setStyleSheet("font-weight: bold; color: #555555; margin-top: 5px;")
        point_layout.addWidget(list_label)

        self.bottom_point_list_widget = QListWidget()
        self.bottom_point_list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background: white;
                min-height: 100px;
                max-height: 150px;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
            }
        """)
        self.bottom_point_list_widget.setSpacing(1)
        point_layout.addWidget(self.bottom_point_list_widget)

        self.bottom_point_count_label = QLabel("总计: 0 个点")
        self.bottom_point_count_label.setStyleSheet("color: #666666; font-size: 11px;")
        point_layout.addWidget(self.bottom_point_count_label)

        parent_layout.addWidget(point_group)

    def setup_export_section(self, parent_layout):
        """设置导出功能区域"""
        export_group = QGroupBox("💾 数据导出")
        export_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #FF9800;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #E65100;
            }
        """)
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(5)

        # ---- 导出按钮行（并排） ----
        button_row = QHBoxLayout()
        button_row.setSpacing(5)

        # 导出Log格式按钮
        self.export_log_btn = QPushButton("📄 导出Log")
        self.export_log_btn.setStyleSheet("""
            QPushButton {
                background: #FF9800;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #F57C00;
            }
            QPushButton:pressed {
                background: #E65100;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.export_log_btn.clicked.connect(self.export_log_format)
        self.export_log_btn.setEnabled(False)
        button_row.addWidget(self.export_log_btn)

        # 导出JSON格式按钮
        self.export_json_btn = QPushButton("📊 导出JSON")
        self.export_json_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """)
        self.export_json_btn.clicked.connect(self.export_json_format)
        self.export_json_btn.setEnabled(False)
        button_row.addWidget(self.export_json_btn)

        export_layout.addLayout(button_row)

        # 导出信息标签
        self.export_info_label = QLabel("导出: 等待数据...")
        self.export_info_label.setStyleSheet("color: #666666; font-size: 11px; padding: 3px;")
        self.export_info_label.setAlignment(Qt.AlignCenter)
        export_layout.addWidget(self.export_info_label)

        parent_layout.addWidget(export_group)

    def export_log_format(self):
        """导出Log格式（人类可读的文本格式）"""
        try:
            top_points = self.controller.get_point_manager().get_points()
            bottom_points = self.controller.get_bottom_point_manager().get_points_with_index()
            all_bottom_points_flat = []
            for pts in bottom_points.values():
                all_bottom_points_flat.extend(pts)

            if not top_points and not all_bottom_points_flat:
                self.show_warning("提示", "没有可导出的数据！请先记录至少一个点。")
                return

            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存Log格式数据",
                "output.log",
                "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*)"
            )

            if not file_path:
                return

            export_content = self._generate_log_content(top_points, bottom_points)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(export_content)

            self.export_info_label.setText(f"✅ Log导出成功: {os.path.basename(file_path)}")
            self.export_info_label.setStyleSheet("color: #2E7D32; font-size: 11px; padding: 3px;")
            self.show_status_message(f"Log数据已导出到 {file_path}")

        except Exception as e:
            self.show_error("导出失败", f"导出Log格式时发生错误：\n{str(e)}")
            self.export_info_label.setText("❌ 导出失败")
            self.export_info_label.setStyleSheet("color: #C62828; font-size: 11px; padding: 3px;")

    def export_json_format(self):
        """导出JSON格式（机器可读的JSON格式）"""
        try:
            import json
            from datetime import datetime

            top_points = self.controller.get_point_manager().get_points()
            bottom_points = self.controller.get_bottom_point_manager().get_points_with_index()
            all_bottom_points_flat = []
            for pts in bottom_points.values():
                all_bottom_points_flat.extend(pts)

            if not top_points and not all_bottom_points_flat:
                self.show_warning("提示", "没有可导出的数据！请先记录至少一个点。")
                return

            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存JSON格式数据",
                "output.json",
                "JSON文件 (*.json);;所有文件 (*)"
            )

            if not file_path:
                return

            json_data = self._generate_json_content(top_points, bottom_points)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            self.export_info_label.setText(f"✅ JSON导出成功: {os.path.basename(file_path)}")
            self.export_info_label.setStyleSheet("color: #2E7D32; font-size: 11px; padding: 3px;")
            self.show_status_message(f"JSON数据已导出到 {file_path}")

        except Exception as e:
            self.show_error("导出失败", f"导出JSON格式时发生错误：\n{str(e)}")
            self.export_info_label.setText("❌ 导出失败")
            self.export_info_label.setStyleSheet("color: #C62828; font-size: 11px; padding: 3px;")

    def _generate_log_content(self, top_points, bottom_points) -> str:
        """生成Log格式内容（人类可读）"""
        from datetime import datetime

        lines = []

        lines.append("=" * 60)
        lines.append("断层扫描点标注数据导出 (Log格式)")
        lines.append("=" * 60)
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 统计信息
        lines.append("-" * 60)
        lines.append("统计信息")
        lines.append("-" * 60)
        total_bottom_points = sum(len(pts) for pts in bottom_points.values())
        lines.append(f"上方图片点数: {len(top_points)}")
        lines.append(f"下方图片总点数: {total_bottom_points}")
        lines.append(f"总计点数: {len(top_points) + total_bottom_points}")
        lines.append(f"有标注的图片数: {len(bottom_points)}")
        lines.append("")

        # 上方点数据
        lines.append("-" * 60)
        lines.append("上方图片点数据 (坐标: 像素)")
        lines.append("-" * 60)
        if top_points:
            lines.append(f"{'序号':<6} {'X坐标':<10} {'Y坐标':<10} {'颜色(R,G,B)':<20} {'大小(px)':<10}")
            lines.append("-" * 60)
            for i, (x, y, color, size) in enumerate(top_points, 1):
                color_str = f"({color[0]},{color[1]},{color[2]})"
                lines.append(f"{i:<6} {x:<10} {y:<10} {color_str:<20} {size:<10}")
        else:
            lines.append("(无数据)")
        lines.append("")

        # 下方点数据（按图片索引分组）
        lines.append("-" * 60)
        lines.append("下方图片点数据 (按图片索引分组)")
        lines.append("-" * 60)

        if bottom_points:
            total_images = len(self.controller.bottom_image_paths)
            lines.append(f"总图片数: {total_images}")
            lines.append(f"有点的图片数: {len(bottom_points)}")
            lines.append("")

            for img_idx in sorted(bottom_points.keys()):
                points = bottom_points[img_idx]
                lines.append(f"图片 {img_idx + 1}:")
                lines.append(f"  点数: {len(points)}")
                if points:
                    lines.append(f"  {'序号':<6} {'X坐标':<10} {'Y坐标':<10} {'颜色(R,G,B)':<20} {'大小(px)':<10}")
                    for i, (x, y, color, size) in enumerate(points, 1):
                        color_str = f"({color[0]},{color[1]},{color[2]})"
                        lines.append(f"  {i:<6} {x:<10} {y:<10} {color_str:<20} {size:<10}")
                lines.append("")
        else:
            lines.append("(无数据)")
        lines.append("")

        lines.append("=" * 60)
        lines.append("导出完成")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_json_content(self, top_points, bottom_points) -> dict:
        """生成JSON格式内容（机器可读）"""
        from datetime import datetime

        total_bottom_points = sum(len(pts) for pts in bottom_points.values())

        json_data = {
            "export_info": {
                "format": "json",
                "export_time": datetime.now().isoformat(),
                "version": "1.0"
            },
            "statistics": {
                "top_count": len(top_points),
                "bottom_count": total_bottom_points,
                "total": len(top_points) + total_bottom_points,
                "images_with_points": len(bottom_points)
            },
            "top_points": [
                {
                    "x": x,
                    "y": y,
                    "color": {"r": c[0], "g": c[1], "b": c[2]},
                    "size": s
                }
                for x, y, c, s in top_points
            ],
            "bottom_points_by_image": {
                str(idx + 1): [
                    {
                        "x": x,
                        "y": y,
                        "color": {"r": c[0], "g": c[1], "b": c[2]},
                        "size": s
                    }
                    for x, y, c, s in points
                ]
                for idx, points in bottom_points.items()
            }
        }

        return json_data

    # ========== 下方点颜色选择 ==========

    def choose_bottom_point_color(self):
        """打开颜色选择对话框（下方点）"""
        current_color = QColor(self.bottom_point_color[0], self.bottom_point_color[1], self.bottom_point_color[2])
        color = QColorDialog.getColor(current_color, self, "选择点的颜色")

        if color.isValid():
            self.bottom_point_color = (color.red(), color.green(), color.blue())
            self.bottom_color_picker_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgb({self.bottom_point_color[0]}, {self.bottom_point_color[1]}, {self.bottom_point_color[2]});
                    border-radius: 4px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    border: 2px solid #666666;
                }}
            """)

    # ========== 下方点大小变化 ==========

    def on_bottom_point_size_changed(self, value):
        """下方点大小滑块变化时的处理"""
        self.bottom_point_size_label.setText(f"{value}px")

    def on_point_item_double_clicked(self, index, x, y):
        """上方点列表双击事件 - 跳转到该点位置"""
        # 更新当前坐标
        self.controller.set_coordinate(x, y)

        # 刷新上方图片显示（绘制十字准星）
        self.draw_crosshair(x, y)

        # 切换下方图片到对应的Y坐标
        self.switch_bottom_image_by_y(y)

        # 启用记录按钮
        self.record_point_btn.setEnabled(True)

        # 显示状态消息
        self.show_status_message(f"已跳转到点 {index + 1}: ({x}, {y})")

        # 在列表中高亮显示该条目
        self.point_list_widget.setCurrentRow(index)

    def on_bottom_point_item_double_clicked(self, index, x, y):
        """下方点列表双击事件 - 跳转到该点位置"""
        # 获取当前图片索引
        current_img_index = self.controller.current_bottom_index
        if current_img_index is None:
            return

        # 更新当前坐标（x保持不变，y使用该点的y坐标）
        self.controller.current_x = x
        self.controller.current_bottom_y = y * self.controller.compress_ratio

        # 更新当前Y坐标（用于上方图片的十字准星）
        if self.controller.current_y is None:
            self.controller.current_y = y
        else:
            # 注意：下方点的y是原始坐标，需要确保与当前显示的图片对应
            # 如果当前显示的图片索引对应的Y坐标就是该点的y坐标
            self.controller.current_y = y

        # 更新窗口标题
        self.setWindowTitle(f"Tomography Point Picker - X={x}, Y={y}")

        # 刷新上方图片显示（绘制十字准星）
        if self.controller.current_x is not None and self.controller.current_y is not None:
            self.draw_crosshair(self.controller.current_x, self.controller.current_y)

        # 刷新下方图片显示（绘制绿线和点）
        self.refresh_bottom_image()

        # 启用记录按钮
        self.record_bottom_point_btn.setEnabled(True)
        self.record_point_btn.setEnabled(True)

        # 显示状态消息
        self.show_status_message(f"已跳转到下方点 {index + 1}: ({x}, {y}) (图片 {current_img_index + 1})")

        # 在列表中高亮显示该条目
        self.bottom_point_list_widget.setCurrentRow(index)

    # ========== 下方点管理功能 ==========

    def record_bottom_current_point(self):
        """记录当前下方图片点击位置的点"""
        if self.controller.current_x is None or self.controller.current_bottom_y is None:
            self.show_warning("提示", "请先在下方的图中点击选择一个位置")
            return

        if self.controller.current_bottom_index is None:
            self.show_warning("提示", "请先加载底部图片")
            return

        x = self.controller.current_x
        y = int(self.controller.current_bottom_y / self.controller.compress_ratio)
        current_size = self.bottom_point_size_slider.value()
        current_index = self.controller.current_bottom_index

        if self.controller.get_bottom_point_manager().add_point(x, y, self.bottom_point_color, current_size):
            self.update_bottom_point_list()
            self.refresh_bottom_image()
            self.show_status_message(
                f"下方已记录点 (图片{current_index + 1}) ({x}, {y}) 颜色: RGB{self.bottom_point_color} 大小: {current_size}px")
            # 启用"清空全部"按钮
            if hasattr(self, 'clear_all_bottom_points_btn'):
                self.clear_all_bottom_points_btn.setEnabled(True)
        else:
            self.show_warning("提示", f"点 ({x}, {y}) 已存在")

    def delete_bottom_point(self, index):
        """删除指定索引的下方点"""
        if self.controller.current_bottom_index is None:
            return

        if self.controller.get_bottom_point_manager().remove_point(index):
            self.update_bottom_point_list()
            self.refresh_bottom_image()
            self.show_status_message(f"已删除下方点 {index + 1} (图片{self.controller.current_bottom_index + 1})")

    def clear_all_bottom_points(self):
        """清空当前图片的所有下方点"""
        if self.controller.current_bottom_index is None:
            return

        if self.controller.get_bottom_point_manager().get_point_count() == 0:
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            f"确定要删除当前图片（索引 {self.controller.current_bottom_index + 1}）的所有已记录的点吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.controller.get_bottom_point_manager().clear_points()
            self.update_bottom_point_list()
            self.refresh_bottom_image()
            self.show_status_message(f"已清空当前图片的所有下方点")

    def clear_all_bottom_points_all_images(self):
        """清空所有图片的下方点"""
        if self.controller.get_bottom_point_manager().get_total_point_count() == 0:
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要删除所有图片的所有已记录的点吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.controller.get_bottom_point_manager().clear_all_points()
            self.update_bottom_point_list()
            self.refresh_bottom_image()
            self.show_status_message("已清空所有图片的所有下方点")

    def update_bottom_point_list(self):
        """更新下方点列表显示"""
        self.bottom_point_list_widget.clear()

        # 获取当前图片的点
        points = self.controller.get_bottom_point_manager().get_points()
        current_index = self.controller.current_bottom_index

        # 显示当前图片索引信息
        if current_index is not None:
            total_images = len(self.controller.bottom_image_paths)
            self.bottom_point_count_label.setText(f"当前图片 {current_index + 1}/{total_images}: {len(points)} 个点")
        else:
            self.bottom_point_count_label.setText("未加载图片")

        for i, (x, y, color, size) in enumerate(points):
            item = QListWidgetItem(self.bottom_point_list_widget)
            item_widget = PointListItem(i, x, y, color, size, self.delete_bottom_point, "bottom")
            # ★★★ 设置双击回调 ★★★
            item_widget.set_double_click_callback(self.on_bottom_point_item_double_clicked)
            item.setSizeHint(item_widget.sizeHint())
            self.bottom_point_list_widget.addItem(item)
            self.bottom_point_list_widget.setItemWidget(item, item_widget)

        # 更新按钮状态
        current_count = len(points)
        self.clear_bottom_points_btn.setEnabled(current_count > 0)

        # 检查是否有任何图片有点
        total_count = self.controller.get_bottom_point_manager().get_total_point_count()
        if hasattr(self, 'clear_all_bottom_points_btn'):
            self.clear_all_bottom_points_btn.setEnabled(total_count > 0)

        self._update_export_button_state()

        # 更新样式
        if current_count > 0:
            self.bottom_point_list_widget.setStyleSheet("""
                QListWidget {
                    border: 1px solid #2196F3;
                    border-radius: 4px;
                    background: white;
                    min-height: 100px;
                    max-height: 150px;
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
            self.bottom_point_list_widget.setStyleSheet("""
                QListWidget {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background: white;
                    min-height: 100px;
                    max-height: 150px;
                }
                QListWidget::item {
                    padding: 2px;
                    border-bottom: 1px solid #eeeeee;
                }
                QListWidget::item:selected {
                    background: #e3f2fd;
                }
            """)

    def _update_export_button_state(self):
        """更新导出按钮状态"""
        # 确保导出按钮已初始化
        if not hasattr(self, 'export_log_btn') or self.export_log_btn is None:
            return
        if not hasattr(self, 'export_json_btn') or self.export_json_btn is None:
            return

        top_count = self.controller.get_point_manager().get_point_count()
        bottom_count = self.controller.get_bottom_point_manager().get_total_point_count()
        has_data = top_count > 0 or bottom_count > 0

        try:
            self.export_log_btn.setEnabled(has_data)
            self.export_json_btn.setEnabled(has_data)

            if has_data and hasattr(self, 'export_info_label') and self.export_info_label:
                self.export_info_label.setText(f"📊 可导出: 上方 {top_count} 个, 下方 {bottom_count} 个")
                self.export_info_label.setStyleSheet("color: #2E7D32; font-size: 11px; padding: 3px;")
            elif hasattr(self, 'export_info_label') and self.export_info_label:
                self.export_info_label.setText("导出: 等待数据...")
                self.export_info_label.setStyleSheet("color: #666666; font-size: 11px; padding: 3px;")
        except Exception as e:
            print(f"更新导出按钮状态时出错: {e}")

    def refresh_bottom_image(self):
        """刷新下方图片显示（重新绘制所有下方点）"""
        if self.controller.bottom_image is None:
            return

        # 重新绘制下方图片
        img_copy = self.controller.bottom_image.copy()
        draw = ImageDraw.Draw(img_copy)

        # 绘制绿线
        if self.controller.current_x is not None:
            # 获取映射后的x坐标
            orig_width, _ = self.controller.bottom_image.size
            compress_ratio = self.controller.get_compress_ratio()
            compressed_height = int(self.controller.app.bottom_height * compress_ratio)
            scale_x = self.controller.app.bottom_width / orig_width
            mapped_x = int(self.controller.current_x * scale_x)
            mapped_x = max(0, min(mapped_x, self.controller.app.bottom_width - 1))
            draw.line([(mapped_x, 0), (mapped_x, compressed_height - 1)], fill=(0, 255, 0), width=2)

        # 绘制下方点（考虑压缩映射）
        self.draw_bottom_recorded_points(draw)

        self.controller.bottom_line_image = img_copy
        self.update_bottom_display_with_line()

    def draw_bottom_recorded_points(self, draw):
        """在下方图片上绘制所有已记录的点（考虑压缩映射）"""
        points = self.controller.get_bottom_point_manager().get_points()
        if not points:
            return

        compress_ratio = self.controller.get_compress_ratio()

        for x, y, color, size in points:
            # 获取图片尺寸
            if self.controller.bottom_image is None:
                return

            img_width, img_height = self.controller.bottom_image.size

            # 将原始坐标映射到压缩后的显示坐标
            # X坐标按比例映射
            orig_width = self.controller.app.bottom_width  # 原始宽度512
            scale_x = img_width / orig_width
            display_x = int(x * scale_x)

            # Y坐标按压缩比例映射
            display_y = int(y * compress_ratio)

            # 确保在有效范围内
            display_x = max(0, min(display_x, img_width - 1))
            display_y = max(0, min(display_y, img_height - 1))

            radius = size // 2
            draw.ellipse(
                [(display_x - radius, display_y - radius),
                 (display_x + radius, display_y + radius)],
                fill=color
            )

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

        self.top_image_label = ClickableImageLabel(
            self.on_top_image_click,
            self.on_top_image_drag  # 新增拖动处理
        )
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
        self.bottom_image_label = ClickableImageLabel(
            self.on_bottom_image_click,
            self.on_bottom_image_drag  # 新增拖动处理
        )
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
        """上方图片点击事件"""
        self._update_top_coordinate(x, y)

    def on_top_image_drag(self, x, y):
        """上方图片拖动事件 - 实时更新坐标"""
        self._update_top_coordinate(x, y)

    def on_bottom_image_click(self, x, y):
        """下方图片点击事件"""
        self._update_bottom_coordinate(x, y)

    def on_bottom_image_drag(self, x, y):
        """下方图片拖动事件 - 实时更新坐标"""
        self._update_bottom_coordinate(x, y)

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
        """绘制十字准星"""
        # 使用图层管理器合成图像
        composite = self.controller.render_top_image()

        if composite is None:
            return

        draw = ImageDraw.Draw(composite)

        # 绘制十字准星
        line_x = x_coord - 1
        if line_x < 0:
            line_x = 0
        draw.line([(line_x, 0), (line_x, self.top_size - 1)], fill=(0, 255, 0), width=2)

        line_y = y_coord - 1
        if line_y < 0:
            line_y = 0
        draw.line([(0, line_y), (self.top_size - 1, line_y)], fill=(255, 0, 0), width=2)

        # 绘制已记录的点
        self.draw_recorded_points(draw)

        self.top_line_photo = self.set_label_image(self.top_image_label, composite)
        self.draw_bottom_line(x_coord)

    def draw_recorded_points(self, draw):
        """在图片上绘制所有已记录的点"""
        points = self.controller.get_point_manager().get_points()
        if not points:
            return

        # 从图层管理器获取图片尺寸
        img_width = self.top_size
        img_height = self.top_size

        for x, y, color, size in points:
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

        self.refresh_bottom_image()

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

            # 重新绘制下方图片（包含绿线和所有下方点）
            img_copy = self.controller.bottom_image.copy()
            draw = ImageDraw.Draw(img_copy)

            # 绘制绿线
            if self.controller.current_x is not None:
                orig_width, _ = self.controller.bottom_image.size
                compress_ratio = self.controller.get_compress_ratio()
                compressed_height = int(self.controller.app.bottom_height * compress_ratio)
                scale_x = self.controller.app.bottom_width / orig_width
                mapped_x = int(self.controller.current_x * scale_x)
                mapped_x = max(0, min(mapped_x, self.controller.app.bottom_width - 1))
                draw.line([(mapped_x, 0), (mapped_x, compressed_height - 1)], fill=(0, 255, 0), width=2)

            # 绘制当前图片的下方点
            self.draw_bottom_recorded_points(draw)

            self.controller.bottom_line_image = img_copy
            self.update_bottom_display_with_line()

            # 恢复滚动位置
            self.bottom_scroll_area.verticalScrollBar().setValue(current_scroll_pos)

            # 更新点列表显示
            self.update_bottom_point_list()

    def update_top_display(self):
        """更新上方图片显示（使用图层管理器）"""
        self.refresh_top_display()

    def update_bottom_display(self):
        """更新下方图片的显示"""
        if self.controller.bottom_image is None:
            return

        display_image = self.controller.bottom_image
        self.bottom_display_photo = self.set_label_image(self.bottom_image_label, display_image)

    # ========== 文件加载方法 ==========
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
                self.update_layer_list()
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
                contrast_top = self.contrast_top_slider.value() / 100.0
                contrast_bottom = self.contrast_bottom_slider.value() / 100.0
                self.controller.set_contrast_top(contrast_top)
                self.controller.set_contrast_bottom(contrast_bottom)

                compress_value = self.compress_slider.value() / 100.0
                self.controller.set_compress_ratio(compress_value)

                self.update_layer_list()
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
            self.refresh_top_display()  # 使用新的刷新方法
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

        for i, (x, y, color, size) in enumerate(points):
            item = QListWidgetItem(self.point_list_widget)
            item_widget = PointListItem(i, x, y, color, size, self.delete_point, "top")
            # ★★★ 设置双击回调 ★★★
            item_widget.set_double_click_callback(self.on_point_item_double_clicked)
            item.setSizeHint(item_widget.sizeHint())
            self.point_list_widget.addItem(item)
            self.point_list_widget.setItemWidget(item, item_widget)

        count = len(points)
        self.point_count_label.setText(f"总计: {count} 个点")
        self.clear_points_btn.setEnabled(count > 0)

        self._update_export_button_state()

        # 更新样式
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

    def _update_top_coordinate(self, x, y):
        """更新上方图片坐标（供点击和拖动调用）"""
        # 检查是否有任何图层或底座
        if self.controller.layer_manager.get_layer_count() == 0 and self.controller.layer_manager.base_image is None:
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

        # 计算显示比例
        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        display_width = int(pixmap_width * ratio)
        display_height = int(pixmap_height * ratio)

        # 计算偏移量
        offset_x = (label_width - display_width) // 2
        offset_y = (label_height - display_height) // 2

        # 转换为图片坐标
        img_x = x - offset_x
        img_y = y - offset_y

        if img_x < 0 or img_x >= display_width or img_y < 0 or img_y >= display_height:
            return

        # 获取原始图片尺寸（使用合成图像的尺寸）
        # 从图层管理器获取第一个图层或底座的尺寸
        orig_width = self.top_size
        orig_height = self.top_size

        original_x = int((img_x / display_width) * orig_width)
        original_y = int((img_y / display_height) * orig_height)

        original_x = max(1, min(orig_width, original_x))
        original_y = max(1, min(orig_height, original_y))

        # 更新坐标
        self.controller.set_coordinate(original_x, original_y)

        # 刷新显示 - 使用新的合成方法
        self.refresh_top_display()
        self.switch_bottom_image_by_y(original_y)

        self.record_point_btn.setEnabled(True)

    def _update_bottom_coordinate(self, x, y):
        """更新下方图片坐标（供点击和拖动调用）"""
        if self.controller.bottom_image is None:
            return

        # 获取label的实际尺寸
        label_width = self.bottom_image_label.width()
        label_height = self.bottom_image_label.height()

        pixmap = self.bottom_image_label.pixmap()
        if pixmap is None:
            return

        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        if label_width <= 0 or label_height <= 0 or pixmap_width <= 0 or pixmap_height <= 0:
            return

        ratio = min(label_width / pixmap_width, label_height / pixmap_height)
        display_width = int(pixmap_width * ratio)
        display_height = int(pixmap_height * ratio)

        if x < 0 or x >= display_width or y < 0 or y >= display_height:
            return

        orig_width, orig_height = self.controller.bottom_image.size

        original_x = int((x / display_width) * orig_width)
        original_y = int((y / display_height) * orig_height)

        original_x = max(1, min(orig_width, original_x))
        original_y = max(1, min(orig_height, original_y))

        self.controller.current_x = original_x
        self.controller.current_bottom_y = original_y
        if self.controller.current_y is None:
            self.controller.current_y = 0

        self.setWindowTitle(f"Tomography Point Picker - X={original_x}, Y={self.controller.current_y}")

        if self.controller.current_y is not None:
            self.draw_crosshair(original_x, self.controller.current_y)

        self.draw_bottom_line(original_x)

        self.record_point_btn.setEnabled(True)
        self.record_bottom_point_btn.setEnabled(True)

    def load_additional_top_image(self):
        """加载额外的上方图片（作为新图层）"""
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要叠加的图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;所有文件 (*)",
        )
        if image_path:
            if self.controller.load_top_image(image_path):
                self.update_layer_list()
                # 如果有坐标，重新绘制
                if self.controller.current_x is not None and self.controller.current_y is not None:
                    self.draw_crosshair(self.controller.current_x, self.controller.current_y)
                else:
                    self.refresh_top_display()
                self.show_status_message(f"已加载图层: {os.path.basename(image_path)}")

    def update_layer_list(self):
        """更新图层列表显示（只显示叠加图层，不包含底图）"""
        self.layer_list_widget.clear()

        # 只获取叠加图层，不包含底图
        layers = self.controller.layer_manager.get_layers()

        if not layers:
            # 没有叠加图层时显示提示
            item = QListWidgetItem(self.layer_list_widget)
            label = QLabel("暂无叠加图层")
            label.setStyleSheet("color: #999999; padding: 10px; text-align: center;")
            label.setAlignment(Qt.AlignCenter)
            item.setSizeHint(label.sizeHint())
            self.layer_list_widget.addItem(item)
            self.layer_list_widget.setItemWidget(item, label)
            self.clear_layers_btn.setEnabled(False)
            return

        # 从上层到下层显示（反转顺序）
        # 显示列表索引: 0 对应 实际列表最后一个（最上层）
        # 显示列表索引: layer_count-1 对应 实际列表第一个（最下层）
        for display_idx in range(len(layers) - 1, -1, -1):
            actual_idx = display_idx  # 实际索引就是循环变量
            layer = layers[actual_idx]

            item = QListWidgetItem(self.layer_list_widget)

            # 创建自定义widget
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 2, 5, 2)
            layout.setSpacing(5)

            # 图层名称
            name_label = QLabel(f"{layer.name}")
            name_label.setStyleSheet("font-weight: 500;")
            layout.addWidget(name_label, 1)

            # 透明度滑块
            opacity_slider = QSlider(Qt.Horizontal)
            opacity_slider.setRange(0, 100)
            opacity_slider.setValue(layer.opacity)
            opacity_slider.setFixedWidth(80)
            # 使用display_idx作为参数传递
            opacity_slider.valueChanged.connect(
                lambda value, idx=display_idx: self.on_layer_opacity_changed(idx, value)
            )
            layout.addWidget(opacity_slider)

            # 透明度数值
            opacity_label = QLabel(f"{layer.opacity}%")
            opacity_label.setFixedWidth(35)
            opacity_label.setStyleSheet("font-size: 10px;")
            layout.addWidget(opacity_label)

            # 存储控件引用以便更新
            widget.opacity_slider = opacity_slider
            widget.opacity_label = opacity_label

            item.setSizeHint(widget.sizeHint())
            self.layer_list_widget.addItem(item)
            self.layer_list_widget.setItemWidget(item, widget)

        # 更新按钮状态
        has_layers = len(layers) > 0
        self.clear_layers_btn.setEnabled(has_layers)

    def on_layer_opacity_changed(self, display_index: int, value: int):
        """图层透明度变化"""
        try:
            # 获取实际图层数量（只包含叠加图层，不包含底图）
            layer_count = self.controller.layer_manager.get_layer_count()
            if layer_count == 0:
                return

            # 显示列表是反转的，所以：
            # display_index 0 对应实际索引 layer_count - 1
            # display_index layer_count - 1 对应实际索引 0
            actual_index = layer_count - 1 - display_index

            # 确保索引有效
            if actual_index < 0 or actual_index >= layer_count:
                return

            # 设置透明度（actual_index是叠加图层的索引，从0开始）
            if self.controller.layer_manager.set_layer_opacity(display_index, value):
                # 更新显示
                self.refresh_top_display()

                # 更新透明度标签
                item = self.layer_list_widget.item(actual_index)
                if item:
                    widget = self.layer_list_widget.itemWidget(item)
                    if widget and hasattr(widget, 'opacity_label'):
                        widget.opacity_label.setText(f"{value}%")
        except Exception as e:
            print(f"透明度调整错误: {e}")

    def clear_all_layers(self):
        """清空所有图层（保留底座图片）"""
        if self.controller.layer_manager.get_layer_count() == 0:
            self.show_warning("提示", "没有可清空的图层")
            return

        reply = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空所有叠加的图层吗？（底座图片将被保留）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # 只清空图层，保留底座
            self.controller.layer_manager.layers.clear()
            self.update_layer_list()
            self.refresh_top_display()
            self.show_status_message("已清空所有叠加图层")

    def refresh_top_display(self):
        """刷新上方图片显示（使用图层管理器合成）"""
        # 获取合成图像
        composite = self.controller.render_top_image()

        # 如果有坐标，绘制十字准星
        if self.controller.current_x is not None and self.controller.current_y is not None:
            draw = ImageDraw.Draw(composite)
            # 绘制十字准星
            line_x = self.controller.current_x - 1
            if line_x < 0:
                line_x = 0
            line_y = self.controller.current_y - 1
            if line_y < 0:
                line_y = 0
            draw.line([(line_x, 0), (line_x, self.top_size - 1)], fill=(0, 255, 0), width=2)
            draw.line([(0, line_y), (self.top_size - 1, line_y)], fill=(255, 0, 0), width=2)
            # 绘制已记录的点
            self.draw_recorded_points(draw)

        # 显示图片
        self.top_photo = self.set_label_image(self.top_image_label, composite)