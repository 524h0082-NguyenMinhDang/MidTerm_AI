import os
import sys
import random
from typing import List, Tuple
from state import SokobanMap, SokobanProblem, SokobanState
from search import uniform_cost_search, a_star_search
from heuristics import MazeDistanceHeuristic

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_benchmark(maps: List[str]):
    """Compare performance of UCS and A* across test maps."""
    print("=" * 85)
    print("REQUIREMENT 3: TIME & SPACE COMPLEXITY COMPARISON (UCS vs A*)")
    print("=" * 85)

    header = f"{'Map':<22} | {'Algorithm':<9} | {'Success':<8} | {'Cost (Steps)':<12} | {'Expanded':<9} | {'Generated':<9} | {'Time (ms)':<10}"
    print(header)
    print("-" * len(header))

    for map_path in maps:
        if not os.path.exists(map_path):
            continue
        m = SokobanMap(map_path)
        prob = SokobanProblem(m)
        h_obj = MazeDistanceHeuristic(m)

        # 1. Run UCS
        res_ucs = uniform_cost_search(prob, max_expanded=50000)
        cost_str = str(res_ucs.cost) if res_ucs.success else "N/A"
        succ_str = "Yes" if res_ucs.success else "Limit"
        print(f"{os.path.basename(map_path):<22} | {'UCS':<9} | {succ_str:<8} | {cost_str:<12} | {res_ucs.expanded_nodes:<9} | {res_ucs.generated_nodes:<9} | {res_ucs.execution_time_ms:<10.2f}")

        # 2. Run A*
        res_astar = a_star_search(prob, heuristic_fn=h_obj.compute, max_expanded=50000)
        cost_str = str(res_astar.cost) if res_astar.success else "N/A"
        succ_str = "Yes" if res_astar.success else "Limit"
        print(f"{os.path.basename(map_path):<22} | {'A*':<9} | {succ_str:<8} | {cost_str:<12} | {res_astar.expanded_nodes:<9} | {res_astar.generated_nodes:<9} | {res_astar.execution_time_ms:<10.2f}")
        print("-" * len(header))


def verify_admissibility_and_consistency(map_path: str = "map/simple_map.txt", num_samples: int = 15):
    """Verify Admissibility and Consistency properties of the BFS Maze Distance heuristic."""
    if not os.path.exists(map_path):
        map_path = "simple_map.txt"

    print("\n" + "=" * 85)
    print("REQUIREMENT 4: VERIFYING ADMISSIBILITY & CONSISTENCY OF HEURISTIC")
    print(f"Test map: {map_path} (Sample size: {num_samples})")
    print("=" * 85)

    m = SokobanMap(map_path)
    prob = SokobanProblem(m)
    h_obj = MazeDistanceHeuristic(m)

    visited_states: List[SokobanState] = [prob.initial_state]
    transitions: List[Tuple[SokobanState, str, SokobanState, int]] = []
    queue = [prob.initial_state]
    seen = {prob.initial_state}

    while queue and len(visited_states) < 150:
        curr = queue.pop(0)
        for act, nxt, cost in prob.get_successors(curr):
            if nxt not in seen:
                seen.add(nxt)
                visited_states.append(nxt)
                queue.append(nxt)
            transitions.append((curr, act, nxt, cost))

    samples = random.sample(visited_states, min(num_samples, len(visited_states)))
    admissible_pass = 0
    admissible_total = 0

    print("\n--- 1. Testing Admissibility: h(n) <= h*(n) ---")
    print(f"{'No.':<4} | {'h(n)':<8} | {'h*(n) True':<12} | {'h <= h* ?':<12} | {'Note'}")
    print("-" * 65)

    for idx, state in enumerate(samples, 1):
        h_val = h_obj.compute(state)
        sub_prob = SokobanProblem(m)
        sub_prob.initial_state = state
        res = a_star_search(sub_prob, heuristic_fn=h_obj.compute)

        if res.success:
            h_star = float(res.cost)
            is_valid = (h_val <= h_star)
            admissible_total += 1
            if is_valid:
                admissible_pass += 1
            print(f"{idx:<4} | {h_val:<8.1f} | {h_star:<12.1f} | {str(is_valid):<12} | Valid")
        else:
            h_star = float("inf")
            is_valid = (h_val <= h_star)
            admissible_total += 1
            if is_valid:
                admissible_pass += 1
            h_str = "inf" if h_val == float("inf") else f"{h_val:.1f}"
            print(f"{idx:<4} | {h_str:<8} | {'inf':<12} | {str(is_valid):<12} | Deadlock (h* = inf)")

    admissible_rate = (admissible_pass / admissible_total * 100) if admissible_total > 0 else 100
    print(f"\n=> Admissibility Result: {admissible_pass}/{admissible_total} states satisfied ({admissible_rate:.1f}%)")

    print("\n--- 2. Testing Consistency: h(n) - h(n') <= c(n, a, n') = 1 ---")
    sample_transitions = random.sample(transitions, min(50, len(transitions)))
    consistent_pass = 0
    consistent_total = 0

    for curr, act, nxt, cost in sample_transitions:
        h_curr = h_obj.compute(curr)
        h_nxt = h_obj.compute(nxt)

        if h_curr != float("inf") and h_nxt != float("inf"):
            consistent_total += 1
            if h_curr - h_nxt <= cost + 1e-6:
                consistent_pass += 1

    consistent_rate = (consistent_pass / consistent_total * 100) if consistent_total > 0 else 100
    print(f"=> Consistency Result: {consistent_pass}/{consistent_total} transitions satisfied ({consistent_rate:.1f}%)")
    print("=" * 85)


if __name__ == "__main__":
    maps = ["map/simple_map.txt", "map/final_map.txt"]
    run_benchmark(maps)
    verify_admissibility_and_consistency("map/simple_map.txt", num_samples=15)
