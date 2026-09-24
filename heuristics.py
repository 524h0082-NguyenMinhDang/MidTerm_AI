# - Tính chất:
#   + Admissible (chấp nhận được): h(n) <= h*(n) vì mỗi hộp phải đến một đích riêng biệt, và đường đi thực tế
#     của hộp không thể ngắn hơn khoảng cách ngắn nhất trên mê cung.
#   + Consistent (nhất quán): h(n) <= c(n, a, n') + h(n') theo bất đẳng thức tam giác trên đồ thị khoảng cách.
# - Bổ sung kiểm tra Deadlock (góc tường chết): nếu hộp bị đẩy vào góc không phải đích, h = vô cùng.

from collections import deque
from typing import Dict, Tuple, Set, List
from state import SokobanMap, SokobanState


class MazeDistanceHeuristic:
    """
    Tính heuristic dựa trên BFS Maze Distance (khoảng cách thực tế trên bản đồ, tránh tường)
    kết hợp với thuật toán gán cặp tối ưu (Min-Weight Matching) giữa hộp và đích.
    """
    def __init__(self, map_data: SokobanMap):
        self.map = map_data
        self.deadlocks = self._identify_corner_deadlocks()
        self.dist_to_goal: Dict[Tuple[int, int], Dict[Tuple[int, int], int]] = {}
        self._precompute_maze_distances()

    def _identify_corner_deadlocks(self) -> Set[Tuple[int, int]]:
        """
        Tìm các ô góc chết (Deadlock): Ô không phải đích và bị kẹp giữa 2 tường vuông góc.
        Nếu một chiếc hộp bị đẩy vào đây, nó sẽ vĩnh viễn không bao giờ ra được.
        """
        deadlocks = set()
        for r in range(self.map.rows):
            for c in range(self.map.cols):
                pos = (r, c)
                # Bỏ qua tường và bỏ qua các ô đích
                if self.map.is_wall(r, c) or pos in self.map.goals:
                    continue

                # Kiểm tra 4 hướng
                up_wall = self.map.is_wall(r - 1, c)
                down_wall = self.map.is_wall(r + 1, c)
                left_wall = self.map.is_wall(r, c - 1)
                right_wall = self.map.is_wall(r, c + 1)

                # 4 góc vuông tạo bởi tường
                if (up_wall and left_wall) or \
                   (up_wall and right_wall) or \
                   (down_wall and left_wall) or \
                   (down_wall and right_wall):
                    deadlocks.add(pos)

        return deadlocks

    def _precompute_maze_distances(self):
        """
        Dùng BFS tính trước khoảng cách ngắn nhất từ MỌI ô hợp lệ đến từng điểm đích D.
        BFS đảm bảo tính khoảng cách thực tế trên lưới đi quanh tường (không đi xuyên tường).
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for goal in self.map.goals:
            dist_map: Dict[Tuple[int, int], int] = {goal: 0}
            queue = deque([goal])

            while queue:
                curr_r, curr_c = queue.popleft()
                curr_d = dist_map[(curr_r, curr_c)]

                for dr, dc in directions:
                    nr, nc = curr_r + dr, curr_c + dc
                    next_pos = (nr, nc)

                    if not self.map.is_wall(nr, nc) and next_pos not in dist_map:
                        dist_map[next_pos] = curr_d + 1
                        queue.append(next_pos)

            self.dist_to_goal[goal] = dist_map

    def get_maze_dist(self, pos: Tuple[int, int], goal: Tuple[int, int]) -> int:
        """Lấy khoảng cách thực tế trên mê cung từ ô pos đến điểm đích goal."""
        return self.dist_to_goal.get(goal, {}).get(pos, 999999)

    def is_deadlock(self, boxes: Set[Tuple[int, int]]) -> bool:
        """Kiểm tra xem có bất kỳ hộp nào đang nằm ở góc chết (không phải đích) không."""
        for box in boxes:
            if box in self.deadlocks:
                return True
        return False

    def compute(self, state: SokobanState) -> float:
        """
        Tính giá trị heuristic h(n) cho trạng thái.
        Dùng thuật toán gán cặp tối ưu (Min-Weight Bipartite Matching) qua khoảng cách mê cung.
        """
        # 1. Phát hiện Deadlock -> nhánh này vô nghiệm, loại bỏ ngay
        if self.is_deadlock(state.boxes):
            return float("inf")

        boxes = list(state.boxes)
        goals = list(self.map.goals)

        if not boxes or not goals:
            return 0.0

        # 2. Xây dựng ma trận chi phí (Cost matrix) giữa Hộp và Đích bằng BFS Maze Distance
        n = len(boxes)
        m = len(goals)
        cost_matrix = [[self.get_maze_dist(box, goal) for goal in goals] for box in boxes]

        # Kiểm tra nếu có hộp không thể đi tới bất kỳ đích nào (khoảng cách vô cực)
        for r in range(n):
            if all(cost_matrix[r][c] >= 999999 for c in range(m)):
                return float("inf")

        # 3. Thuật toán gán cặp tối ưu (Min-Cost Matching / Hungarian)
        total_dist = self._min_weight_matching(cost_matrix, n, m)
        return float(total_dist)

    def _min_weight_matching(self, cost_matrix: List[List[int]], n: int, m: int) -> int:
        """
        Giải bài toán gán cặp cực tiểu giữa n hộp và m đích (n <= m).
        Cài đặt thuật toán Hungarian thuần Python tối ưu cho n <= 10.
        """
        if n == 0 or m == 0:
            return 0

        # Nếu n <= 8, dùng Hungarian (Kuhn-Munkres)
        # Khởi tạo ma trận vuông kích thước m x m (với m >= n)
        k = max(n, m)
        cost = [[0] * (k + 1) for _ in range(k + 1)]
        for i in range(n):
            for j in range(m):
                cost[i + 1][j + 1] = cost_matrix[i][j]

        # Thuật toán Hungarian O(V^3)
        u = [0] * (k + 1)
        v = [0] * (k + 1)
        p = [0] * (k + 1)
        way = [0] * (k + 1)

        for i in range(1, n + 1):
            p[0] = i
            j0 = 0
            minv = [float("inf")] * (k + 1)
            used = [False] * (k + 1)
            while True:
                used[j0] = True
                i0 = p[j0]
                delta = float("inf")
                j1 = 0
                for j in range(1, m + 1):
                    if not used[j]:
                        cur = cost[i0][j] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j
                for j in range(k + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                j0 = j1
                if p[j0] == 0:
                    break
            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        return -v[0]
