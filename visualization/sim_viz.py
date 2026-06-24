# visualization/sim_viz.py

import pygame
import numpy as np
from configs.config import (
    MAP_WIDTH, MAP_HEIGHT, GRID_DIVISIONS,
    BATTERY_WARNING, BATTERY_CRITICAL, BATTERY_EMERGENCY
)

# ── Screen settings ────────────────────────────────────────────────────────────
SCREEN_W = 900
SCREEN_H = 900
PANEL_W  = 220       # right-side info panel
TOTAL_W  = SCREEN_W + PANEL_W

# ── Colors ────────────────────────────────────────────────────────────────────
C_BG          = (10,  12,  20)
C_GRID        = (30,  35,  55)
C_REGION_LOW  = (20,  40,  20)
C_REGION_MED  = (40,  40,  10)
C_REGION_HIGH = (50,  25,   5)
C_REGION_CRIT = (60,  10,  10)
C_UAV_FULL    = (80, 200, 120)
C_UAV_WARN    = (255,200,  50)
C_UAV_CRIT    = (255, 80,  50)
C_TASK_NORMAL = (60, 130, 220)
C_TASK_HIGH   = (220,150,  30)
C_TASK_EMERG  = (220,  40,  40)
C_MEC         = (160,  80, 220)
C_CHARGE      = (50,  220, 200)
C_TEXT        = (200, 210, 230)
C_PANEL_BG    = (15,  18,  30)

WORKLOAD_COLORS = {
    "LOW":    C_REGION_LOW,
    "MEDIUM": C_REGION_MED,
    "HIGH":   C_REGION_HIGH,
    "CRITICAL": C_REGION_CRIT,
}


def world_to_screen(x, y):
    """Convert world coordinates to screen pixels."""
    sx = int((x / MAP_WIDTH)  * SCREEN_W)
    sy = int((1 - y / MAP_HEIGHT) * SCREEN_H)   # flip Y
    return sx, sy


class SimVisualizer:
    def __init__(self, world, uavs, mec_servers):
        pygame.init()
        self.screen = pygame.display.set_mode((TOTAL_W, SCREEN_H))
        pygame.display.set_caption("UAV HDRL Simulator")
        self.clock  = pygame.time.Clock()
        self.font_s = pygame.font.SysFont("consolas", 11)
        self.font_m = pygame.font.SysFont("consolas", 13)
        self.font_l = pygame.font.SysFont("consolas", 16, bold=True)

        self.world       = world
        self.uavs        = uavs
        self.mec_servers = mec_servers
        self.tasks       = []
        self.sim_time    = 0.0
        self.running     = True

    # ── Main render call ───────────────────────────────────────────────────────
    def render(self, tasks, sim_time):
        self.tasks    = tasks
        self.sim_time = sim_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

        self.screen.fill(C_BG)
        self._draw_regions()
        self._draw_grid()
        self._draw_charging_stations()
        self._draw_mec_servers()
        self._draw_tasks()
        self._draw_uavs()
        self._draw_panel()
        pygame.display.flip()

    # ── Draw subregions ────────────────────────────────────────────────────────
    def _draw_regions(self):
        for r in self.world.regions:
            sx, sy = world_to_screen(r.x_start, r.y_start + r.height)
            pw = int((r.width  / MAP_WIDTH)  * SCREEN_W)
            ph = int((r.height / MAP_HEIGHT) * SCREEN_H)
            base_color = WORKLOAD_COLORS.get(r.workload, C_REGION_LOW)

            # Brighten based on congestion
            brightness = 1.0 + r.congestion * 1.5
            color = tuple(min(int(c * brightness), 255) for c in base_color)
            pygame.draw.rect(self.screen, color, (sx, sy, pw, ph))

            # Region label
            label = self.font_s.render(
                f"R{r.region_id} {r.workload[:1]} T:{len(r.active_tasks)}", True, C_TEXT)
            self.screen.blit(label, (sx + 4, sy + 4))

    # ── Draw grid lines ────────────────────────────────────────────────────────
    def _draw_grid(self):
        step_x = SCREEN_W // GRID_DIVISIONS
        step_y = SCREEN_H // GRID_DIVISIONS
        for i in range(GRID_DIVISIONS + 1):
            pygame.draw.line(self.screen, C_GRID, (i * step_x, 0), (i * step_x, SCREEN_H))
            pygame.draw.line(self.screen, C_GRID, (0, i * step_y), (SCREEN_W, i * step_y))

    # ── Draw tasks ────────────────────────────────────────────────────────────
    def _draw_tasks(self):
        for t in self.tasks:
            if t.status not in ("PENDING", "ASSIGNED"):
                continue
            sx, sy = world_to_screen(t.location[0], t.location[1])
            if t.task_type == "emergency":
                color = C_TASK_EMERG
                size  = 5
            elif t.priority == "high":
                color = C_TASK_HIGH
                size  = 4
            else:
                color = C_TASK_NORMAL
                size  = 3
            pygame.draw.circle(self.screen, color, (sx, sy), size)

    # ── Draw UAVs ─────────────────────────────────────────────────────────────
    def _draw_uavs(self):
        for uav in self.uavs:
            sx, sy = world_to_screen(uav.position[0], uav.position[1])

            # Color by battery state
            if uav.battery_soc > BATTERY_WARNING:
                color = C_UAV_FULL
            elif uav.battery_soc > BATTERY_CRITICAL:
                color = C_UAV_WARN
            else:
                color = C_UAV_CRIT

            # Draw UAV as triangle
            tip   = (sx,      sy - 10)
            left  = (sx - 7,  sy + 6)
            right = (sx + 7,  sy + 6)
            pygame.draw.polygon(self.screen, color, [tip, left, right])
            pygame.draw.polygon(self.screen, C_TEXT, [tip, left, right], 1)

            # Battery bar
            bar_w = 20
            bar_h = 4
            fill  = int((uav.battery_soc / 100.0) * bar_w)
            pygame.draw.rect(self.screen, (60, 60, 60), (sx - 10, sy + 9, bar_w, bar_h))
            pygame.draw.rect(self.screen, color,        (sx - 10, sy + 9, fill,  bar_h))

            # UAV ID
            label = self.font_s.render(f"U{uav.id}", True, C_TEXT)
            self.screen.blit(label, (sx - 8, sy + 15))

            # Draw line to current task
            if uav.current_task and uav.current_task.status == "ASSIGNED":
                tx, ty = world_to_screen(
                    uav.current_task.location[0],
                    uav.current_task.location[1]
                )
                pygame.draw.line(self.screen, (*color, 80), (sx, sy), (tx, ty), 1)

    # ── Draw charging stations ────────────────────────────────────────────────
    def _draw_charging_stations(self):
        for cs in self.world.charging_stations:
            sx, sy = world_to_screen(cs["position"][0], cs["position"][1])
            pygame.draw.rect(self.screen, C_CHARGE, (sx - 6, sy - 6, 12, 12))
            label = self.font_s.render("C", True, C_BG)
            self.screen.blit(label, (sx - 4, sy - 5))

    # ── Draw MEC servers ──────────────────────────────────────────────────────
    def _draw_mec_servers(self):
        for mec in self.mec_servers:
            sx, sy = world_to_screen(mec.position[0], mec.position[1])
            pygame.draw.circle(self.screen, C_MEC, (sx, sy), 8)
            pygame.draw.circle(self.screen, C_TEXT, (sx, sy), 8, 1)
            label = self.font_s.render("M", True, C_BG)
            self.screen.blit(label, (sx - 4, sy - 5))

    # ── Side panel ────────────────────────────────────────────────────────────
    def _draw_panel(self):
        panel_x = SCREEN_W
        pygame.draw.rect(self.screen, C_PANEL_BG, (panel_x, 0, PANEL_W, SCREEN_H))
        pygame.draw.line(self.screen, C_GRID, (panel_x, 0), (panel_x, SCREEN_H), 1)

        y = 10
        def write(text, color=C_TEXT, font=None):
            nonlocal y
            f = font or self.font_m
            self.screen.blit(f.render(text, True, color), (panel_x + 8, y))
            y += 18

        write("UAV SIMULATOR", C_UAV_FULL, self.font_l)
        write(f"Time: {self.sim_time:.1f}s")
        y += 6

        # UAV list
        write("── UAVs ──", C_GRID)
        for uav in self.uavs:
            color = C_UAV_FULL if uav.battery_soc > BATTERY_WARNING else (
                    C_UAV_WARN if uav.battery_soc > BATTERY_CRITICAL else C_UAV_CRIT)
            write(f"U{uav.id} {uav.battery_soc:5.1f}% {uav.battery_status}", color)
            write(f"   {uav.flight_mode}", C_TEXT, self.font_s)

        y += 6

        # Task summary
        pending   = sum(1 for t in self.tasks if t.status == "PENDING")
        assigned  = sum(1 for t in self.tasks if t.status == "ASSIGNED")
        done      = sum(1 for t in self.tasks if t.status == "DONE")
        emergency = sum(1 for t in self.tasks if t.task_type == "emergency")

        write("── Tasks ──", C_GRID)
        write(f"Pending:  {pending}")
        write(f"Assigned: {assigned}")
        write(f"Done:     {done}")
        write(f"Emergency:{emergency}", C_TASK_EMERG)

        y += 6

        # Legend
        write("── Legend ──", C_GRID)
        write("▲ UAV (green=ok)", C_UAV_FULL, self.font_s)
        write("▲ UAV (yellow=warn)", C_UAV_WARN, self.font_s)
        write("● Task normal", C_TASK_NORMAL, self.font_s)
        write("● Task high", C_TASK_HIGH, self.font_s)
        write("● Emergency", C_TASK_EMERG, self.font_s)
        write("■ Charging stn", C_CHARGE, self.font_s)
        write("● MEC server", C_MEC, self.font_s)

    def tick(self, fps=60):
        self.clock.tick(fps)

    def close(self):
        pygame.quit()