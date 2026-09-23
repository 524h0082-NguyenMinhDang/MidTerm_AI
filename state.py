import sys
from typing import Tuple, FrozenSet, List, Set, Optional

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class SokobanMap:
    """Chứa thông tin tĩnh của bản đồ (kích thước, tường, vị trí đích)."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.walls: Set[Tuple[int, int]] = set()
        self.goals: Set[Tuple[int, int]] = set()
        self.initial_agent: Optional[Tuple[int, int]] = None
        self.initial_boxes: Set[Tuple[int, int]] = set()
        self.rows = 0
        self.cols = 0

        self._load_from_file(filepath)

    def _load_from_file(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\r\n") for line in f]

        self.rows = len(lines)
        self.cols = max(len(line) for line in lines) if lines else 0

        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == "%":
                    self.walls.add((r, c))
                elif ch == "D":
                    self.goals.add((r, c))
                elif ch == "A":
                    self.initial_agent = (r, c)
                elif ch == "B":
                    self.initial_boxes.add((r, c))
                elif ch == "C":
                    # C là hộp đang nằm sẵn trên điểm đích
                    self.goals.add((r, c))
                    self.initial_boxes.add((r, c))
                elif ch == " ":
                    pass  # Ô trống

        if self.initial_agent is None:
            raise ValueError(f"Không tìm thấy vị trí agent 'A' trong map: {filepath}")

    def is_wall(self, r: int, c: int) -> bool:
        return (r, c) in self.walls or r < 0 or r >= self.rows or c < 0 or c >= self.cols


class SokobanState:
    """Biểu diễn trạng thái động của game: vị trí Agent và tập vị trí các Hộp."""

    __slots__ = ("agent", "boxes", "_hash")

    def __init__(self, agent: Tuple[int, int], boxes: FrozenSet[Tuple[int, int]]):
        self.agent = agent
        self.boxes = boxes
        self._hash = hash((self.agent, self.boxes))

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SokobanState):
            return False
        return self.agent == other.agent and self.boxes == other.boxes

    def __repr__(self) -> str:
        return f"SokobanState(agent={self.agent}, boxes={sorted(self.boxes)})"


class SokobanProblem:
    """Mô hình hóa bài toán tìm kiếm không gian trạng thái (State-Space Search)."""

    ACTIONS = {
        "North": (-1, 0),
        "South": (1, 0),
        "West": (0, -1),
        "East": (0, 1)
    }

    def __init__(self, sokoban_map: SokobanMap):
        self.map = sokoban_map
        self.initial_state = SokobanState(
            agent=self.map.initial_agent,
            boxes=frozenset(self.map.initial_boxes)
        )

    def is_goal(self, state: SokobanState) -> bool:
        """Kiểm tra điều kiện đích: tất cả các vị trí đích đều có hộp hoặc tất cả hộp đã vào đích."""
        # Mỗi hộp phải nằm ở một vị trí đích
        return state.boxes.issubset(self.map.goals)

    def get_successors(self, state: SokobanState) -> List[Tuple[str, SokobanState, int]]:
        """
        Sinh các trạng thái kế tiếp.
        Trả về danh sách các tuple: (action_name, next_state, step_cost).
        """
        successors: List[Tuple[str, SokobanState, int]] = []
        ar, ac = state.agent

        for action_name, (dr, dc) in self.ACTIONS.items():
            new_ar, new_ac = ar + dr, ac + dc

            # Không thể đi vào tường
            if self.map.is_wall(new_ar, new_ac):
                continue

            # Trường hợp ô kế tiếp có hộp: Agent phải đẩy hộp
            if (new_ar, new_ac) in state.boxes:
                new_br, new_bc = new_ar + dr, new_ac + dc

                # Hộp không thể bị đẩy vào tường hoặc đẩy vào một hộp khác
                if self.map.is_wall(new_br, new_bc) or (new_br, new_bc) in state.boxes:
                    continue

                # Tạo tập vị trí hộp mới sau khi đẩy
                new_boxes = set(state.boxes)
                new_boxes.remove((new_ar, new_ac))
                new_boxes.add((new_br, new_bc))

                next_state = SokobanState((new_ar, new_ac), frozenset(new_boxes))
                successors.append((action_name, next_state, 1))

            # Trường hợp ô kế tiếp là ô trống
            else:
                next_state = SokobanState((new_ar, new_ac), state.boxes)
                successors.append((action_name, next_state, 1))

        return successors

    def to_string(self, state: SokobanState) -> str:
        """Vẽ lại trạng thái hiện tại dưới dạng chuỗi ký tự."""
        output_rows = []
        for r in range(self.map.rows):
            chars = []
            for c in range(self.map.cols):
                pos = (r, c)
                if pos in self.map.walls:
                    chars.append("%")
                elif pos == state.agent:
                    chars.append("A")
                elif pos in state.boxes and pos in self.map.goals:
                    chars.append("C")
                elif pos in state.boxes:
                    chars.append("B")
                elif pos in self.map.goals:
                    chars.append("D")
                else:
                    chars.append(" ")
            output_rows.append("".join(chars))
        return "\n".join(output_rows)