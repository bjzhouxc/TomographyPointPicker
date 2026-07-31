from PIL import Image, ImageDraw, ImageFont
from PySide6.QtGui import QImage, QPixmap


class ImageUtils:
    """图片处理工具类"""

    @staticmethod
    def pil_to_pixmap(image):
        """将PIL图片转换为QPixmap"""
        rgb_image = image.convert("RGB")
        width, height = rgb_image.size
        data = rgb_image.tobytes("raw", "RGB")
        qimage = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888).copy()
        return QPixmap.fromImage(qimage)

    @staticmethod
    def resize_and_center_with_info(image, target_size):
        """调整图片到目标尺寸并居中（保持比例）"""
        target_width, target_height = target_size

        resized_image = Image.new("RGB", (target_width, target_height), (255, 255, 255))

        scaled_image = image.resize(target_size, Image.Resampling.LANCZOS)

        x = (target_width - target_width) // 2
        y = (target_height - target_height) // 2
        resized_image.paste(scaled_image, (x, y))

        display_info = {
            "display_width": target_width,
            "display_height": target_height,
            "offset_x": x,
            "offset_y": y,
        }

        return resized_image, display_info

    @staticmethod
    def create_placeholder(width, height, color=(240, 240, 240)):
        """创建占位图"""
        return Image.new("RGB", (width, height), color)

    @staticmethod
    def draw_crosshair(image, x, y, color_vertical=(0, 255, 0), color_horizontal=(255, 0, 0), width=2):
        """在图片上绘制十字准星"""
        draw = ImageDraw.Draw(image)

        # 垂直线
        line_x = x - 1
        draw.line([(line_x, 0), (line_x, image.height - 1)], fill=color_vertical, width=width)

        # 水平线
        line_y = y - 1
        draw.line([(0, line_y), (image.width - 1, line_y)], fill=color_horizontal, width=width)

        return image

    @staticmethod
    def draw_vertical_line(image, x, color=(0, 255, 0), width=2):
        """在图片上绘制垂直线"""
        # 确保图片是 RGB 模式
        if image.mode != 'RGB':
            image = image.convert('RGB')

        draw = ImageDraw.Draw(image)
        line_x = x - 1
        draw.line([(line_x, 0), (line_x, image.height - 1)], fill=color, width=width)
        return image

    @staticmethod
    def blend_images(base_image, overlay_image, opacity):
        # 如果没有覆盖图，返回底图
        if overlay_image is None:
            return base_image.copy()

        # 如果没有底图，直接返回覆盖图
        if base_image is None:
            return overlay_image.copy()

        # 确保透明度在有效范围内
        opacity = max(0, min(100, opacity))

        # 如果覆盖图与底图尺寸不同，调整覆盖图大小
        if overlay_image.size != base_image.size:
            overlay_resized = overlay_image.resize(base_image.size, Image.Resampling.LANCZOS)
        else:
            overlay_resized = overlay_image

        # 根据透明度决定显示方式
        if opacity >= 100:
            # 完全显示底图
            return base_image.copy()
        elif opacity <= 0:
            # 完全显示覆盖图（透明度为0时，覆盖图完全不透明）
            return overlay_resized.copy()
        else:
            # 混合显示
            overlay_weight = 1.0 - (opacity / 100.0)
            return Image.blend(base_image, overlay_resized, overlay_weight)