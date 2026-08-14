import glob
import os
import re
from typing import Optional, Tuple, List

from PIL import Image
from PySide6.QtWidgets import QMessageBox

from ..models.point_manager import PointManager, BottomPointManager
from ..models.image_layer_manager import ImageLayerManager
from ..utils import ImageUtils


class ImageController:
    """图像控制器，处理图像加载和操作逻辑"""

    def __init__(self, app):
        self.app = app
        self.point_manager = PointManager()
        self.bottom_point_manager = BottomPointManager()

        # 图层管理器
        self.layer_manager = ImageLayerManager((app.top_size, app.top_size))

        # 图像数据（保留兼容性）
        self.top_image: Optional[Image.Image] = None
        self.base_image: Optional[Image.Image] = None
        self.bottom_image: Optional[Image.Image] = None
        self.bottom_line_image: Optional[Image.Image] = None

        # 显示参数
        self.top_display_width = 0
        self.top_display_height = 0
        self.top_offset_x = 0
        self.top_offset_y = 0

        # 当前坐标
        self.current_x: Optional[int] = None
        self.current_y: Optional[int] = None
        self.current_bottom_y: Optional[int] = None

        # 底部图片路径列表
        self.bottom_image_paths: List[str] = []

        # 压缩比例
        self.compress_ratio = 1.0

        # 对比度
        self.contrast_top = 1.0
        self.contrast_bottom = 1.0

        # 当前显示的底部图片索引
        self.current_bottom_index: Optional[int] = None

    def load_top_image(self, image_path: str) -> bool:
        """加载上方图片（作为新图层添加到最上面）"""
        try:
            original_image = Image.open(image_path)
            # 添加到图层管理器
            layer_index = self.layer_manager.add_layer(
                original_image,
                opacity=100,  # 默认完全不透明
                name=os.path.basename(image_path)
            )

            # 更新显示信息（使用第一个图层的信息）
            if self.layer_manager.get_layer_count() > 0:
                first_layer = self.layer_manager.get_layer(0)
                if first_layer:
                    # 计算显示信息
                    resized_image, display_info = ImageUtils.resize_and_center_with_info(
                        first_layer.image, (self.app.top_size, self.app.top_size)
                    )
                    self.top_display_width = display_info["display_width"]
                    self.top_display_height = display_info["display_height"]
                    self.top_offset_x = display_info["offset_x"]
                    self.top_offset_y = display_info["offset_y"]

            self.app.setWindowTitle(f"Tomography Point Picker - 已加载 {self.layer_manager.get_layer_count()} 层")
            return True
        except Exception as e:
            self.app.show_error("错误", f"加载图片失败：\n{str(e)}")
            return False

    def load_data_folder(self, base_path: str) -> bool:
        """加载数据文件夹"""
        try:
            # 加载Angio作为底座
            angio_path = os.path.join(base_path, "Angio")
            if os.path.exists(angio_path):
                png_files = glob.glob(os.path.join(angio_path, "*.png"))
                if png_files:
                    image_path = png_files[0]
                    original_image = Image.open(image_path)
                    self.layer_manager.set_base_image(original_image)

                    # 设置显示信息
                    resized_image, display_info = ImageUtils.resize_and_center_with_info(
                        original_image, (self.app.top_size, self.app.top_size)
                    )
                    self.top_display_width = display_info["display_width"]
                    self.top_display_height = display_info["display_height"]
                    self.top_offset_x = display_info["offset_x"]
                    self.top_offset_y = display_info["offset_y"]

            # 加载B-scan
            bscan_path = os.path.join(base_path, "B-scan_PixelRatio")
            if not os.path.exists(bscan_path):
                self.app.show_error("错误", f"找不到B-scan_PixelRatio文件夹：\n{bscan_path}")
                return False

            png_files = sorted(glob.glob(os.path.join(bscan_path, "*.png")))
            if not png_files:
                self.app.show_error("错误", f"B-scan_PixelRatio文件夹中没有png图片：\n{bscan_path}")
                return False

            self.bottom_image_paths = sorted(png_files, key=self._sort_by_number)

            # 初始化底部点管理器
            self.current_bottom_index = 0
            self.bottom_point_manager.set_current_index(0)

            self.app.setWindowTitle(f"Tomography Point Picker - Angio + B-scan已加载 ({len(png_files)}张)")
            return True
        except Exception as e:
            self.app.show_error("错误", f"加载失败：\n{str(e)}")
            return False

    def _sort_by_number(self, filename):
        """按文件名中的数字排序"""
        match = re.search(r"_(\d+)\.png$", filename)
        if match:
            return int(match.group(1))
        return 0

    def set_coordinate(self, x: int, y: int):
        """设置当前坐标"""
        self.current_x = x
        self.current_y = y
        self.app.setWindowTitle(f"Tomography Point Picker - X={x}, Y={y}")

    def get_coordinate(self) -> Tuple[Optional[int], Optional[int]]:
        """获取当前坐标"""
        return self.current_x, self.current_y

    def switch_bottom_image_by_y(self, y_coord: int) -> bool:
        """根据Y坐标切换底部图片"""
        if not self.bottom_image_paths:
            return False

        index = y_coord - 1
        if index < 0 or index >= len(self.bottom_image_paths):
            return False

        self.current_bottom_index = index
        self.bottom_point_manager.set_current_index(index)

        try:
            image_path = self.bottom_image_paths[index]
            original_image = Image.open(image_path)
            resized_image, _ = ImageUtils.resize_and_center_with_info(
                original_image, (
                    self.app.bottom_width, int(self.app.bottom_height * self.get_compress_ratio())
                )
            )
            resized_image = ImageUtils.adjust_contrast(resized_image, self.contrast_bottom)

            self.bottom_image = resized_image

            if self.current_x is not None:
                img_copy = resized_image.copy()
                ImageUtils.draw_vertical_line(img_copy, self.current_x)
                self.bottom_line_image = img_copy
            else:
                self.bottom_line_image = None

            return True
        except Exception as e:
            self.app.show_error("错误", f"加载图片失败：\n{str(e)}")
            return False

    def get_point_manager(self) -> PointManager:
        return self.point_manager

    def set_compress_ratio(self, ratio: float):
        self.compress_ratio = ratio

    def get_compress_ratio(self) -> float:
        return self.compress_ratio

    def set_contrast_top(self, value: float):
        self.contrast_top = max(0.0, min(2.0, value))

    def get_contrast_top(self) -> float:
        return self.contrast_top

    def set_contrast_bottom(self, value: float):
        self.contrast_bottom = max(0.0, min(2.0, value))

    def get_contrast_bottom(self) -> float:
        return self.contrast_bottom

    def get_bottom_point_manager(self) -> BottomPointManager:
        return self.bottom_point_manager

    def get_compressed_height(self) -> int:
        return int(self.app.bottom_height * self.compress_ratio)

    def get_layer_manager(self) -> ImageLayerManager:
        """获取图层管理器"""
        return self.layer_manager

    def render_top_image(self) -> Image.Image:
        """渲染合成后的上方图片"""
        # 获取合成图像
        composite = self.layer_manager.render_composite()
        # 应用对比度
        return ImageUtils.adjust_contrast(composite, self.contrast_top)