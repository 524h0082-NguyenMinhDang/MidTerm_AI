# Đặc điểm:
#     Cấu trúc Graph Search để tránh duyệt lại các trạng thái đã xét.
#     Sử dụng Priority Queue (heapq) có bộ đếm tự tăng để tránh so sánh trực tiếp các đối tượng State.

import heapq
import time
from typing import List, Tuple, Optional, Callable
from state import SokobanProblem, SokobanState, SokobanMap
from heuristics import MazeDistanceHeuristic


class SearchResult:
    def __init__(self,
                 actions: Optional[List[str]],
                 states: Optional[List[SokobanState]],
                 cost: int,
                 expanded_nodes: int,
                 generated_nodes: int,
                 execution_time_ms: float,
                 algorithm_name: str):
        self.actions = actions
        self.states = states
        self.cost = cost
        self.expanded_nodes = expanded_nodes
        self.generated_nodes = generated_nodes
        self.execution_time_ms = execution_time_ms
        self.algorithm_name = algorithm_name
        self.success = actions is not None


class SearchNode:
    """Nút trong cây tìm kiếm."""

    def __init__(self,
                 state: SokobanState,
                 parent: Optional["SearchNode"] = None,
                 action: Optional[str] = None,
                 g_cost: int = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.g_cost = g_cost


def reconstruct_path(node: SearchNode) -> Tuple[List[str], List[SokobanState]]:
    """Truy vết ngược từ Goal Node về Root Node để lấy chuỗi hành động và danh sách trạng thái."""
    actions = []
    states = []
    curr = node
    while curr is not None:
        states.append(curr.state)
        if curr.action is not None:
            actions.append(curr.action)
        curr = curr.parent

    actions.reverse()
    states.reverse()
    return actions, states


def uniform_cost_search(problem: SokobanProblem, max_expanded: int = 300000) -> SearchResult:
    """
    Thuật toán Uniform Cost Search (UCS).
    Độ ưu tiên trong hàng đợi là g(n) (chi phí tích lũy từ gốc đến n).
    """
    start_time = time.perf_counter()

    initial_node = SearchNode(state=problem.initial_state, g_cost=0)
    if problem.is_goal(initial_node.state):
        elapsed = (time.perf_counter() - start_time) * 1000
        return SearchResult([], [initial_node.state], 0, 0, 1, elapsed, "UCS")

    counter = 0
    frontier = []
    heapq.heappush(frontier, (0, counter, initial_node))

    explored = {initial_node.state: 0}
    expanded_nodes = 0
    generated_nodes = 1

    while frontier:
        g, _, current_node = heapq.heappop(frontier)

        if g > explored.get(current_node.state, float("inf")):
            continue

        expanded_nodes += 1

        if problem.is_goal(current_node.state):
            elapsed = (time.perf_counter() - start_time) * 1000
            actions, states = reconstruct_path(current_node)
            return SearchResult(actions, states, current_node.g_cost, expanded_nodes, generated_nodes, elapsed, "UCS")

        if expanded_nodes >= max_expanded:
            break

        for action, next_state, step_cost in problem.get_successors(current_node.state):
            new_g = current_node.g_cost + step_cost
            generated_nodes += 1

            if next_state not in explored or new_g < explored[next_state]:
                explored[next_state] = new_g
                child_node = SearchNode(state=next_state, parent=current_node, action=action, g_cost=new_g)
                counter += 1
                heapq.heappush(frontier, (new_g, counter, child_node))

    elapsed = (time.perf_counter() - start_time) * 1000
    return SearchResult(None, None, -1, expanded_nodes, generated_nodes, elapsed, "UCS")


def a_star_search(problem: SokobanProblem,
                  heuristic_fn: Optional[Callable[[SokobanState], float]] = None,
                  max_expanded: int = 300000) -> SearchResult:
    """
    Thuật toán A* Search.
    Độ ưu tiên trong hàng đợi là f(n) = g(n) + h(n).
    """
    start_time = time.perf_counter()

    if heuristic_fn is None:
        h_obj = MazeDistanceHeuristic(problem.map)
        heuristic_fn = h_obj.compute

    initial_node = SearchNode(state=problem.initial_state, g_cost=0)
    if problem.is_goal(initial_node.state):
        elapsed = (time.perf_counter() - start_time) * 1000
        return SearchResult([], [initial_node.state], 0, 0, 1, elapsed, "A*")

    h0 = heuristic_fn(initial_node.state)
    if h0 == float("inf"):
        elapsed = (time.perf_counter() - start_time) * 1000
        return SearchResult(None, None, -1, 0, 1, elapsed, "A*")

    counter = 0
    frontier = []
    heapq.heappush(frontier, (h0, h0, counter, initial_node))

    explored = {initial_node.state: 0}
    expanded_nodes = 0
    generated_nodes = 1

    while frontier:
        f, h, _, current_node = heapq.heappop(frontier)

        if current_node.g_cost > explored.get(current_node.state, float("inf")):
            continue

        expanded_nodes += 1

        if problem.is_goal(current_node.state):
            elapsed = (time.perf_counter() - start_time) * 1000
            actions, states = reconstruct_path(current_node)
            return SearchResult(actions, states, current_node.g_cost, expanded_nodes, generated_nodes, elapsed, "A*")

        if expanded_nodes >= max_expanded:
            break

        for action, next_state, step_cost in problem.get_successors(current_node.state):
            new_g = current_node.g_cost + step_cost
            generated_nodes += 1

            if next_state not in explored or new_g < explored[next_state]:
                h_val = heuristic_fn(next_state)
                # Bỏ qua trạng thái bế tắc (deadlock)
                if h_val == float("inf"):
                    continue

                explored[next_state] = new_g
                child_node = SearchNode(state=next_state, parent=current_node, action=action, g_cost=new_g)
                new_f = new_g + h_val
                counter += 1
                heapq.heappush(frontier, (new_f, h_val, counter, child_node))

    elapsed = (time.perf_counter() - start_time) * 1000
    return SearchResult(None, None, -1, expanded_nodes, generated_nodes, elapsed, "A*")