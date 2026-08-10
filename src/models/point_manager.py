from typing import List, Tuple, Dict, Optional


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
    """下方图片点管理器 - 按图片索引分别存储"""

    def __init__(self):
        # 使用字典存储每个图片索引对应的点列表
        # key: 图片索引 (0-based), value: List of (x, y, color, size)
        self.points_by_index: Dict[int, List[Tuple[int, int, Tuple[int, int, int], int]]] = {}
        # 当前显示的图片索引
        self.current_index: Optional[int] = None

    def set_current_index(self, index: int):
        """设置当前显示的图片索引"""
        if index < 0:
            return
        self.current_index = index
        # 如果该索引还没有对应的列表，创建一个空列表
        if index not in self.points_by_index:
            self.points_by_index[index] = []

    def get_current_index(self) -> Optional[int]:
        """获取当前图片索引"""
        return self.current_index

    def add_point(self, x: int, y: int, color: Tuple[int, int, int], size: int) -> bool:
        """在当前图片上添加点"""
        if self.current_index is None:
            return False

        # 确保当前索引存在
        if self.current_index not in self.points_by_index:
            self.points_by_index[self.current_index] = []

        # 检查是否已存在相同坐标的点
        points = self.points_by_index[self.current_index]
        for px, py, _, _ in points:
            if px == x and py == y:
                return False

        points.append((x, y, color, size))
        return True

    def remove_point(self, index: int) -> bool:
        """删除当前图片中指定索引的点"""
        if self.current_index is None:
            return False

        points = self.points_by_index.get(self.current_index, [])
        if 0 <= index < len(points):
            points.pop(index)
            return True
        return False

    def clear_points(self, index: Optional[int] = None):
        """清空指定索引或当前图片的所有点"""
        if index is not None:
            if index in self.points_by_index:
                self.points_by_index[index].clear()
        elif self.current_index is not None:
            if self.current_index in self.points_by_index:
                self.points_by_index[self.current_index].clear()

    def clear_all_points(self):
        """清空所有图片的点"""
        self.points_by_index.clear()

    def get_points(self, index: Optional[int] = None) -> List[Tuple[int, int, Tuple[int, int, int], int]]:
        """获取指定索引或当前图片的点列表"""
        if index is not None:
            return self.points_by_index.get(index, []).copy()
        elif self.current_index is not None:
            return self.points_by_index.get(self.current_index, []).copy()
        return []

    def get_points_with_index(self) -> Dict[int, List[Tuple[int, int, Tuple[int, int, int], int]]]:
        """获取所有图片的点数据"""
        return {idx: pts.copy() for idx, pts in self.points_by_index.items() if pts}

    def get_point_count(self, index: Optional[int] = None) -> int:
        """获取指定索引或当前图片的点数量"""
        if index is not None:
            return len(self.points_by_index.get(index, []))
        elif self.current_index is not None:
            return len(self.points_by_index.get(self.current_index, []))
        return 0

    def get_total_point_count(self) -> int:
        """获取所有图片的总点数"""
        return sum(len(pts) for pts in self.points_by_index.values())

    def has_points(self, index: Optional[int] = None) -> bool:
        """检查指定索引或当前图片是否有点"""
        return self.get_point_count(index) > 0