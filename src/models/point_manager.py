from typing import List, Tuple


class PointManager:
    """上方图片点管理器"""

    def __init__(self):
        # 存储 (x, y, color, size)
        self.points: List[Tuple[int, int, Tuple[int, int, int], int]] = []

    def add_point(self, x: int, y: int, color: Tuple[int, int, int], size: int) -> bool:
        for px, py, _, _ in self.points:
            if px == x and py == y:
                return False
        self.points.append((x, y, color, size))
        return True

    def remove_point(self, index: int) -> bool:
        if 0 <= index < len(self.points):
            self.points.pop(index)
            return True
        return False

    def clear_points(self):
        self.points.clear()

    def get_points(self) -> List[Tuple[int, int, Tuple[int, int, int], int]]:
        return self.points.copy()

    def get_point_count(self) -> int:
        return len(self.points)


class BottomPointManager:
    """下方图片点管理器 - 存储原始坐标 (x, y)"""

    def __init__(self):
        # 存储 (x, y, color, size) - x和y是原始图片坐标
        self.points: List[Tuple[int, int, Tuple[int, int, int], int]] = []

    def add_point(self, x: int, y: int, color: Tuple[int, int, int], size: int) -> bool:
        for px, py, _, _ in self.points:
            if px == x and py == y:
                return False
        self.points.append((x, y, color, size))
        return True

    def remove_point(self, index: int) -> bool:
        if 0 <= index < len(self.points):
            self.points.pop(index)
            return True
        return False

    def clear_points(self):
        self.points.clear()

    def get_points(self) -> List[Tuple[int, int, Tuple[int, int, int], int]]:
        return self.points.copy()

    def get_point_count(self) -> int:
        return len(self.points)

    def get_compressed_y(self, y: int, compress_ratio: float) -> int:
        """将原始Y坐标转换为压缩后的显示Y坐标"""
        return int(y * compress_ratio)

    def get_original_y(self, compressed_y: int, compress_ratio: float) -> int:
        """将压缩后的显示Y坐标转换回原始Y坐标"""
        if compress_ratio == 0:
            return 0
        return int(compressed_y / compress_ratio)