import pygame
from configs import config

MAP_PIXELS = 900
PANEL_WIDTH = 260
WINDOW_WIDTH = MAP_PIXELS + PANEL_WIDTH
WINDOW_HEIGHT = MAP_PIXELS

COLORS = {
    "background": (18, 18, 24),
    "panel_bg": (28, 28, 36),
    "grid_line": (60, 60, 70),
    "text": (230, 230, 230),
    "workload_LOW": (60, 140, 70),
    "workload_MEDIUM": (200, 190, 60),
    "workload_HIGH": (220, 140, 40),
    "workload_CRITICAL": (150, 30, 30),
    "task_normal": (80, 140, 230),
    "task_high": (230, 150, 40),
    "task_emergency": (230, 60, 60),
    "uav_ok": (70, 220, 100),
    "uav_warning": (230, 210, 60),
    "uav_critical": (230, 70, 70),
    "charging_station": (60, 220, 220),
    "mec_server": (170, 100, 230),
}


class SimVisualizer:
    def __init__(self, world, uavs, mec_servers):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("UAV-HDRL Simulator -- Single UAV Demo")
        self.world = world
        self.uavs = uavs
        self.mec_servers = mec_servers
        self.clock = pygame.time.Clock()
        self.running = True

        self.font_small = pygame.font.SysFont("consolas", 13)
        self.font_medium = pygame.font.SysFont("consolas", 16, bold=True)
        self.font_large = pygame.font.SysFont("consolas", 20, bold=True)

    def world_to_screen(self, x, y):
        sx = int((x / config.MAP_WIDTH) * MAP_PIXELS)
        sy = int(MAP_PIXELS - (y / config.MAP_HEIGHT) * MAP_PIXELS)  # flip Y
        return sx, sy

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def render(self, tasks, sim_time):
        self.handle_events()
        if not self.running:
            return
        self.screen.fill(COLORS["background"])
        self._draw_regions()
        self._draw_grid()
        self._draw_tasks(tasks)
        self._draw_charging_stations()
        self._draw_mec_servers()
        self._draw_uavs()
        self._draw_panel(tasks, sim_time)
        pygame.display.flip()

    def _draw_regions(self):
        for region in self.world.regions:
            x0, y0 = self.world_to_screen(region.x_start, region.y_start + region.height)
            x1, y1 = self.world_to_screen(region.x_start + region.width, region.y_start)
            base_color = COLORS[f"workload_{region.workload}"]
            brightness = 1.0 + 0.5 * region.congestion
            color = tuple(min(int(c * brightness), 255) for c in base_color)
            rect = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
            pygame.draw.rect(self.screen, color, rect)

            label = f"R{region.region_id} {region.workload[0]} T:{len(region.active_tasks)}"
            text_surf = self.font_small.render(label, True, (255, 255, 255))
            self.screen.blit(text_surf, (x0 + 6, y0 + 6))

    def _draw_grid(self):
        divisions = config.GRID_DIVISIONS
        for i in range(divisions + 1):
            x = int(i * MAP_PIXELS / divisions)
            pygame.draw.line(self.screen, COLORS["grid_line"], (x, 0), (x, MAP_PIXELS), 1)
            y = int(i * MAP_PIXELS / divisions)
            pygame.draw.line(self.screen, COLORS["grid_line"], (0, y), (MAP_PIXELS, y), 1)

    def _draw_tasks(self, tasks):
        for task in tasks:
            if task.status not in ("PENDING", "ASSIGNED"):
                continue
            x, y = self.world_to_screen(task.location[0], task.location[1])
            if task.task_type == "emergency":
                color = COLORS["task_emergency"]
                radius = 6
            elif task.priority == "high":
                color = COLORS["task_high"]
                radius = 5
            else:
                color = COLORS["task_normal"]
                radius = 4
            pygame.draw.circle(self.screen, color, (x, y), radius)

    def _draw_uavs(self):
        for uav in self.uavs:
            x, y = self.world_to_screen(uav.position[0], uav.position[1])
            if uav.battery_status in ("FULL", "NORMAL"):
                color = COLORS["uav_ok"]
            elif uav.battery_status == "WARNING":
                color = COLORS["uav_warning"]
            else:
                color = COLORS["uav_critical"]

            points = [(x, y - 10), (x - 8, y + 8), (x + 8, y + 8)]
            pygame.draw.polygon(self.screen, color, points)

            # Battery bar
            bar_w = 24
            fill_w = int(bar_w * uav.battery_soc / 100.0)
            pygame.draw.rect(self.screen, (80, 80, 80), (x - bar_w // 2, y + 12, bar_w, 4))
            pygame.draw.rect(self.screen, color, (x - bar_w // 2, y + 12, fill_w, 4))

            if uav.current_task is not None:
                tx, ty = self.world_to_screen(*uav.current_task.location)
                pygame.draw.line(self.screen, (120, 120, 200), (x, y), (tx, ty), 1)

            label = self.font_small.render(f"UAV{uav.id}", True, (255, 255, 255))
            self.screen.blit(label, (x - 12, y + 18))

    def _draw_charging_stations(self):
        for cs in self.world.charging_stations:
            x, y = self.world_to_screen(cs["position"][0], cs["position"][1])
            pygame.draw.rect(self.screen, COLORS["charging_station"], (x - 8, y - 8, 16, 16))
            label = self.font_small.render("C", True, (0, 0, 0))
            self.screen.blit(label, (x - 4, y - 7))

    def _draw_mec_servers(self):
        for server in self.mec_servers:
            x, y = self.world_to_screen(server.position[0], server.position[1])
            pygame.draw.circle(self.screen, COLORS["mec_server"], (x, y), 10)
            label = self.font_small.render("M", True, (0, 0, 0))
            self.screen.blit(label, (x - 4, y - 7))

    def _draw_panel(self, tasks, sim_time):
        panel_rect = pygame.Rect(MAP_PIXELS, 0, PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, COLORS["panel_bg"], panel_rect)

        y = 16
        title = self.font_large.render("Single UAV Demo", True, COLORS["text"])
        self.screen.blit(title, (MAP_PIXELS + 16, y))
        y += 34

        time_text = self.font_medium.render(f"t = {sim_time:6.1f}s", True, COLORS["text"])
        self.screen.blit(time_text, (MAP_PIXELS + 16, y))
        y += 30

        for uav in self.uavs:
            lines = [
                f"UAV {uav.id}",
                f"  SOC: {uav.battery_soc:5.1f}%  [{uav.battery_status}]",
                f"  Mode: {uav.flight_mode}",
                f"  Task: {uav.current_task.task_id if uav.current_task else '-'}",
            ]
            for line in lines:
                surf = self.font_small.render(line, True, COLORS["text"])
                self.screen.blit(surf, (MAP_PIXELS + 16, y))
                y += 18
            y += 8

        pending = sum(1 for t in tasks if t.status == "PENDING")
        assigned = sum(1 for t in tasks if t.status == "ASSIGNED")
        done = sum(1 for t in tasks if t.status == "DONE")
        emergency = sum(1 for t in tasks if t.task_type == "emergency")

        y += 8
        for line in [
            f"Pending:  {pending}",
            f"Assigned: {assigned}",
            f"Done:     {done}",
            f"Emergency:{emergency}",
        ]:
            surf = self.font_small.render(line, True, COLORS["text"])
            self.screen.blit(surf, (MAP_PIXELS + 16, y))
            y += 18

        y += 16
        legend = [
            ("Task (normal)", COLORS["task_normal"]),
            ("Task (high)", COLORS["task_high"]),
            ("Task (emergency)", COLORS["task_emergency"]),
            ("Charging station", COLORS["charging_station"]),
            ("MEC server", COLORS["mec_server"]),
        ]
        for label, color in legend:
            pygame.draw.circle(self.screen, color, (MAP_PIXELS + 22, y + 6), 5)
            surf = self.font_small.render(label, True, COLORS["text"])
            self.screen.blit(surf, (MAP_PIXELS + 36, y))
            y += 20

    def tick(self, fps=60):
        self.clock.tick(fps * config.VIZ_SPEED)
