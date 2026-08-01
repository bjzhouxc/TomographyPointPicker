from typing import List, Tuple

class PointManager:
    """管理记录的点"""

    def __init__(self):
        self.points: List[Tuple[int, int, Tuple[int, int, int], int]] = []
        self.point_size = 5  # 默认点大小（直径）

    def add_point(self, x: int, y: int, color: Tuple[int, int, int], size: int):
        """添加点，如果已存在则返回False"""
        for px, py, _, _ in self.points:
            if px == x and py == y:
                return False
        self.points.append((x, y, color, size))
        return True

    def remove_point(self, index: int):
        """删除点，如果索引无效则返回False"""
        if 0 <= index < len(self.points):
            self.points.pop(index)
            return True
        return False

    def clear_points(self):
        """清空所有点"""
        self.points.clear()

    def get_points(self) -> List[Tuple[int, int, Tuple[int, int, int], int]]:
        """获取所有点"""
        return self.points.copy()

    def get_point_count(self) -> int:
        """获取点的数量"""
        return len(self.points)

    def set_point_size(self, size: int):
        """设置点的大小"""
        self.point_size = max(1, size)  # 最小为1

    def get_point_size(self) -> int:
        """获取点的大小"""
        return self.point_size