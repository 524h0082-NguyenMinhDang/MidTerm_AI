import os
import sys
import pygame
from state import SokobanMap, SokobanProblem
from search import uniform_cost_search, a_star_search
from heuristics import MazeDistanceHeuristic

pygame.init()
pygame.font.init()

ASSET_DIR, MAP_DIR = "asset", "map"
FONT = pygame.font.SysFont("Arial, sans-serif", 15)
FONT_BOLD = pygame.font.SysFont("Arial, sans-serif", 15, bold=True)
FONT_TITLE = pygame.font.SysFont("Arial, sans-serif", 20, bold=True)

# Minimalist, clean color palette
BG_COLOR = (28, 28, 28)
PANEL_COLOR = (36, 36, 36)
BORDER_COLOR = (55, 55, 55)
TEXT_COLOR = (240, 240, 240)
MUTED_TEXT = (160, 160, 160)
BTN_BG = (50, 50, 50)
BTN_ACTIVE = (45, 110, 190)


def get_maps():
    if not os.path.exists(MAP_DIR):
        os.makedirs(MAP_DIR, exist_ok=True)
    maps = [os.path.join(MAP_DIR, f) for f in os.listdir(MAP_DIR) if f.endswith(".txt")]
    return sorted(maps) if maps else ["example_map.txt"]


class SokobanGUI:
    """Minimalist, compact Sokoban GUI with a 3-step wizard workflow."""

    def __init__(self, map_path=None):
        self.w, self.h = 1280, 720
        self.board_w = 880
        self.screen = pygame.display.set_mode((self.w, self.h))
        self.clock = pygame.time.Clock()

        self.maps = get_maps()
        self.map_idx = self.maps.index(map_path) if map_path in self.maps else 0

        # Load raw sprites
        self.raw_sprites = {}
        names = {"agent": "A_agent.png", "box": "B_Box.png", "box_placed": "C_darkBox.png",
                 "goal": "D_Position.png", "floor": "blank.png", "wall": "wall.png"}
        for k, v in names.items():
            p = os.path.join(ASSET_DIR, v)
            self.raw_sprites[k] = pygame.image.load(p).convert_alpha() if os.path.exists(p) else None

        # Wizard state (1: Choose Map, 2: Choose Algorithm, 3: Results & Controls)
        self.step = 1
        self.algo = "A*"
        self.load_map(self.maps[self.map_idx])

    def load_map(self, path):
        self.map_path = path
        self.map_data = SokobanMap(path)
        self.problem = SokobanProblem(self.map_data)
        self.heuristic = MazeDistanceHeuristic(self.map_data)

        # Calculate optimal tile size for the left area
        max_tile = min(800 // max(1, self.map_data.cols), 640 // max(1, self.map_data.rows))
        self.tile_size = min(64, max(24, max_tile))
        self.sprites = {k: pygame.transform.smoothscale(img, (self.tile_size, self.tile_size))
                        for k, img in self.raw_sprites.items() if img}

        # Game and search state
        self.state = self.problem.initial_state
        self.sol_states, self.sol_actions = [self.state], []
        self.step_idx = 0
        self.paused = True
        self.res = None
        self.last_tick = 0
        self.has_finished_first_run = False
        pygame.display.set_caption(f"Sokoban AI Solver - {os.path.basename(path)}")

    def solve(self):
        if self.algo == "UCS":
            self.res = uniform_cost_search(self.problem)
        else:
            self.res = a_star_search(self.problem, heuristic_fn=self.heuristic.compute)

        if self.res.success and self.res.states:
            self.sol_states = self.res.states
            self.sol_actions = self.res.actions or []
            self.step_idx = 0
            self.state = self.sol_states[0]
        self.step = 3
        self.paused = True
        self.has_finished_first_run = False

    def draw_btn(self, rect, text, active=False, enabled=True):
        bg = BTN_ACTIVE if active else (BTN_BG if enabled else (40, 40, 40))
        color = TEXT_COLOR if enabled else (100, 100, 100)
        pygame.draw.rect(self.screen, bg, rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER_COLOR, rect, 1, border_radius=4)
        s = FONT_BOLD.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=rect.center))

    def draw_board(self):
        bw = self.map_data.cols * self.tile_size
        bh = self.map_data.rows * self.tile_size
        ox, oy = (self.board_w - bw) // 2, (self.h - bh) // 2

        for r in range(self.map_data.rows):
            for c in range(self.map_data.cols):
                pos = (r, c)
                x, y = ox + c * self.tile_size, oy + r * self.tile_size

                if pos in self.map_data.walls:
                    self.screen.blit(self.sprites["wall"], (x, y))
                else:
                    self.screen.blit(self.sprites["floor"], (x, y))
                    if pos in self.map_data.goals:
                        k = "box_placed" if pos in self.state.boxes else "goal"
                        self.screen.blit(self.sprites[k], (x, y))
                    elif pos in self.state.boxes:
                        self.screen.blit(self.sprites["box"], (x, y))

                    if pos == self.state.agent:
                        self.screen.blit(self.sprites["agent"], (x, y))

        if self.problem.is_goal(self.state):
            win_surf = FONT_BOLD.render("VICTORY: ALL BOXES PLACED!", True, (80, 200, 120))
            self.screen.blit(win_surf, win_surf.get_rect(center=(self.board_w // 2, self.h - 25)))

    def draw_sidebar(self):
        pygame.draw.rect(self.screen, PANEL_COLOR, (self.board_w, 0, self.w - self.board_w, self.h))
        pygame.draw.line(self.screen, BORDER_COLOR, (self.board_w, 0), (self.board_w, self.h), 1)

        x, y = self.board_w + 25, 25
        title = FONT_TITLE.render("SOKOBAN AI", True, (255, 204, 0))
        self.screen.blit(title, (x, y))

        # --- STEP 1: CHOOSE MAP ---
        y += 45
        s1 = FONT_BOLD.render("1. Choose Map" + (" (Confirmed)" if self.step > 1 else ""), True,
                              (80, 200, 120) if self.step > 1 else TEXT_COLOR)
        self.screen.blit(s1, (x, y))

        self.r_prev = pygame.Rect(x, y + 25, 36, 30)
        self.r_next = pygame.Rect(x + 310, y + 25, 36, 30)
        self.draw_btn(self.r_prev, "<", enabled=(self.step == 1))
        self.draw_btn(self.r_next, ">", enabled=(self.step == 1))

        name = os.path.basename(self.map_path)
        lbl = FONT.render(f"{self.map_idx + 1}/{len(self.maps)}: {name}", True, TEXT_COLOR)
        self.screen.blit(lbl, lbl.get_rect(center=(x + 173, y + 40)))

        info = FONT.render(f"Size: {self.map_data.rows}x{self.map_data.cols}  |  Boxes: {len(self.map_data.initial_boxes)}", True, MUTED_TEXT)
        self.screen.blit(info, (x, y + 65))

        self.r_confirm_map = pygame.Rect(x, y + 90, 346, 32)
        if self.step == 1:
            self.draw_btn(self.r_confirm_map, "Confirm Map", active=True)

        # --- STEP 2: CHOOSE ALGORITHM ---
        y += 140
        s2 = FONT_BOLD.render("2. Choose Algorithm" + (" (Selected)" if self.step > 2 else ""), True,
                              (80, 200, 120) if self.step > 2 else (TEXT_COLOR if self.step == 2 else MUTED_TEXT))
        self.screen.blit(s2, (x, y))

        self.r_ucs = pygame.Rect(x, y + 25, 168, 32)
        self.r_astar = pygame.Rect(x + 178, y + 25, 168, 32)
        self.draw_btn(self.r_ucs, "1. UCS", active=(self.algo == "UCS"), enabled=(self.step == 2))
        self.draw_btn(self.r_astar, "2. A*", active=(self.algo == "A*"), enabled=(self.step == 2))

        self.r_confirm_algo = pygame.Rect(x, y + 65, 346, 32)
        if self.step == 2:
            self.draw_btn(self.r_confirm_algo, "Confirm & Run Algorithm", active=True)

        # --- STEP 3: RESULTS & CONTROLS ---
        y += 115
        s3 = FONT_BOLD.render("3. Results & Controls", True, TEXT_COLOR if self.step == 3 else MUTED_TEXT)
        self.screen.blit(s3, (x, y))

        y += 25
        if self.step == 3 and self.res:
            lines = [
                f"Algorithm: {self.algo}",
                f"Status: {'Success' if self.res.success else 'No Solution'}",
                f"Search Time: {self.res.execution_time_ms:.1f} ms",
                f"Expanded Nodes: {self.res.expanded_nodes}",
                f"Total Steps: {max(0, len(self.sol_states) - 1)}",
                f"Current Step: {self.step_idx}/{max(0, len(self.sol_states) - 1)}"
            ]
            for line in lines:
                self.screen.blit(FONT.render(line, True, TEXT_COLOR), (x, y))
                y += 22

            self.r_back = pygame.Rect(x, y + 10, 108, 32)
            self.r_play = pygame.Rect(x + 118, y + 10, 110, 32)
            self.r_fwd = pygame.Rect(x + 238, y + 10, 108, 32)
            self.draw_btn(self.r_back, "Prev", enabled=(self.step_idx > 0))

            # Xác định chữ trên nút Play: chỉ hiện "Play Again" sau khi đã chạy xong lần đầu
            if not self.has_finished_first_run:
                play_text = "Pause" if not self.paused else "Play"
            else:
                if not self.paused:
                    play_text = "Pause"
                elif self.step_idx >= len(self.sol_states) - 1:
                    play_text = "Play Again"
                else:
                    play_text = "Play"

            self.draw_btn(self.r_play, play_text, active=(not self.paused or play_text == "Play Again"))
            self.draw_btn(self.r_fwd, "Next", enabled=(self.step_idx < len(self.sol_states) - 1))
        else:
            self.screen.blit(FONT.render("Complete Step 1 and 2 to view results...", True, MUTED_TEXT), (x, y))

        self.r_reset = pygame.Rect(x, 665, 346, 32)
        self.draw_btn(self.r_reset, "Reset to Step 1", enabled=(self.step > 1))

    def run(self):
        running = True
        while running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False

                # 100% Mouse-driven interaction
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Step 1 clicks
                    if self.step == 1:
                        if self.r_prev.collidepoint(ev.pos):
                            self.map_idx = (self.map_idx - 1) % len(self.maps)
                            self.load_map(self.maps[self.map_idx])
                        elif self.r_next.collidepoint(ev.pos):
                            self.map_idx = (self.map_idx + 1) % len(self.maps)
                            self.load_map(self.maps[self.map_idx])
                        elif self.r_confirm_map.collidepoint(ev.pos):
                            self.step = 2

                    # Step 2 clicks
                    elif self.step == 2:
                        if self.r_ucs.collidepoint(ev.pos):
                            self.algo = "UCS"
                        elif self.r_astar.collidepoint(ev.pos):
                            self.algo = "A*"
                        elif self.r_confirm_algo.collidepoint(ev.pos):
                            self.solve()

                    # Step 3 clicks
                    elif self.step == 3:
                        if self.r_back.collidepoint(ev.pos) and self.step_idx > 0:
                            self.step_idx -= 1
                            self.state = self.sol_states[self.step_idx]
                            self.paused = True
                        elif self.r_fwd.collidepoint(ev.pos) and self.step_idx < len(self.sol_states) - 1:
                            self.step_idx += 1
                            self.state = self.sol_states[self.step_idx]
                            self.paused = True
                        elif self.r_play.collidepoint(ev.pos):
                            if self.step_idx >= len(self.sol_states) - 1:
                                self.step_idx = 0
                                self.state = self.sol_states[0]
                                self.paused = False
                            else:
                                self.paused = not self.paused

                    # Reset to Step 1 click
                    if self.step > 1 and self.r_reset.collidepoint(ev.pos):
                        self.step = 1
                        self.load_map(self.maps[self.map_idx])

            now = pygame.time.get_ticks()
            if self.step == 3 and not self.paused and len(self.sol_states) > 1:
                if now - self.last_tick >= 200:
                    if self.step_idx < len(self.sol_states) - 1:
                        self.step_idx += 1
                        self.state = self.sol_states[self.step_idx]
                        self.last_tick = now
                    else:
                        self.paused = True
                        self.has_finished_first_run = True

            self.screen.fill(BG_COLOR)
            self.draw_board()
            self.draw_sidebar()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()



if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    SokobanGUI(map_path=path).run()
