from typing import List, Tuple

class PointManager:
    """管理记录的点"""

    def __init__(self):
        self.points: List[Tuple[int, int, Tuple[int, int, int]]] = []
        self.point_size = 5  # 点的直径

    def add_point(self, x: int, y: int, color: Tuple[int, int, int]):
        """添加点，如果已存在则返回False"""
        for px, py, _ in self.points:
            if px == x and py == y:
                return False
        self.points.append((x, y, color))
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

    def get_points(self) -> List[Tuple[int, int, Tuple[int, int, int]]]:
        """获取所有点"""
        return self.points.copy()

    def get_point_count(self) -> int:
        """获取点的数量"""
        return len(self.points)