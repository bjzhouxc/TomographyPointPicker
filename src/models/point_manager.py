from typing import List, Tuple

class PointManager:
    """管理记录的点"""

    def __init__(self):
        self.points: List[Tuple[int, int]] = []  # 存储 (x, y) 坐标
        self.point_size = 5  # 点的直径
        self.point_color = (0, 255, 0)

    def add_point(self, x: int, y: int):
        """添加点，如果已存在则返回False"""
        if (x, y) not in self.points:
            self.points.append((x, y))
            return True
        return False

    def remove_point(self, index: int):
        """删除点，如果索引无效则返回False"""
        if 0 <= index < len(self.points):
            self.points.pop(index)
            return True
        return False

    def clear_points(self):
        """清空所有点"""
        self.points.clear()

    def get_points(self) -> List[Tuple[int, int]]:
        """获取所有点"""
        return self.points.copy()

    def get_point_count(self) -> int:
        """获取点的数量"""
        return len(self.points)