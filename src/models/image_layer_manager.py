from typing import List, Optional, Tuple
from PIL import Image
from dataclasses import dataclass


@dataclass
class ImageLayer:
    """图片层数据类"""
    image: Image.Image
    opacity: int  # 0-100
    name: str  # 文件路径或自定义名称
    visible: bool = True

    def get_blend_weight(self) -> float:
        """获取混合权重 (0.0-1.0)"""
        return self.opacity / 100.0


class ImageLayerManager:
    """图片层管理器 - 支持多层图片叠加"""

    def __init__(self, base_size: Tuple[int, int]):
        """
        初始化图层管理器
        Args:
            base_size: 基础尺寸 (width, height)
        """
        self.base_size = base_size
        self.layers: List[ImageLayer] = []
        self.base_image: Optional[Image.Image] = None  # 底座图片（可选）

    def set_base_image(self, image: Image.Image):
        """设置底座图片"""
        if image.size != self.base_size:
            self.base_image = image.resize(self.base_size, Image.Resampling.LANCZOS)
        else:
            self.base_image = image.copy()

    def add_layer(self, image: Image.Image, opacity: int = 100, name: str = "") -> int:
        """
        添加新图层（添加到最上面）
        Returns:
            图层索引
        """
        # 调整图片尺寸
        if image.size != self.base_size:
            resized_image = image.resize(self.base_size, Image.Resampling.LANCZOS)
        else:
            resized_image = image.copy()

        # 生成名称
        if not name:
            name = f"图层 {len(self.layers) + 1}"

        layer = ImageLayer(resized_image, opacity, name)
        self.layers.append(layer)
        return len(self.layers) - 1

    def insert_layer(self, index: int, image: Image.Image, opacity: int = 100, name: str = ""):
        """在指定位置插入图层"""
        if image.size != self.base_size:
            resized_image = image.resize(self.base_size, Image.Resampling.LANCZOS)
        else:
            resized_image = image.copy()

        if not name:
            name = f"图层 {index + 1}"

        layer = ImageLayer(resized_image, opacity, name)
        self.layers.insert(index, layer)

    def remove_layer(self, index: int) -> bool:
        """移除图层"""
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            return True
        return False

    def move_layer(self, from_index: int, to_index: int) -> bool:
        """移动图层位置"""
        if 0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers):
            layer = self.layers.pop(from_index)
            self.layers.insert(to_index, layer)
            return True
        return False

    def set_layer_opacity(self, index: int, opacity: int) -> bool:
        """设置图层透明度"""
        if 0 <= index < len(self.layers):
            self.layers[index].opacity = max(0, min(100, opacity))
            return True
        return False

    def set_layer_visibility(self, index: int, visible: bool) -> bool:
        """设置图层可见性"""
        if 0 <= index < len(self.layers):
            self.layers[index].visible = visible
            return True
        return False

    def get_layer(self, index: int) -> Optional[ImageLayer]:
        """获取图层"""
        if 0 <= index < len(self.layers):
            return self.layers[index]
        return None

    def get_layers(self) -> List[ImageLayer]:
        """获取所有图层"""
        return self.layers.copy()

    def get_layer_count(self) -> int:
        """获取图层数量"""
        return len(self.layers)

    def render_composite(self) -> Image.Image:
        """
        渲染合成图像
        从底层到上层逐层叠加
        """
        # 从底座开始
        if self.base_image:
            result = self.base_image.copy()
            if result.mode == "RGBA":
                result = result.convert('RGB')
        else:
            # 如果没有底座，返回空白图
            result = Image.new("RGB", self.base_size, (255, 255, 255))

        # 逐层叠加
        for layer in self.layers:
            if not layer.visible:
                continue

            if layer.opacity >= 100:
                # 完全不透明，直接覆盖
                result = layer.image.copy()
            elif layer.opacity > 0:
                # 部分透明，混合
                weight = layer.get_blend_weight()
                result = Image.blend(result, layer.image, weight)
            # 透明度为0时，跳过该层

        return result

    def clear(self):
        """清空所有图层"""
        self.layers.clear()
        self.base_image = None