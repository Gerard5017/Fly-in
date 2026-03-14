import os
import pygame
from .map_validator import MapValidator
from .hub import Hub
from typing import Optional
from .metadata import Color, Zone
import colorsys


class Visualiser():
    def __init__(self, map: MapValidator) -> None:
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        pygame.init()

        self.map = map
        self.all_hubs: list[Hub] = self.map.hub[:]
        if self.map.start_hub is not None:
            self.all_hubs.append(self.map.start_hub)
        if self.map.end_hub is not None:
            self.all_hubs.append(self.map.end_hub)

        max_x = max(h.x for h in self.all_hubs)
        max_y = max(h.y for h in self.all_hubs)
        min_x = min(h.x for h in self.all_hubs)
        min_y = min(h.y for h in self.all_hubs)

        self.dif_x = max_x - min_x + 2
        self.dif_y = max_y - min_y + 2

        self.cell_size = min(1800 // self.dif_x, 1800 // self.dif_y)
        self.origin_x = (-min_x + 1) * self.cell_size
        self.origin_y = (-min_y + 1) * self.cell_size

        self.width = self.cell_size * self.dif_x
        self.height = self.cell_size * self.dif_y
        self.screen = pygame.display.set_mode((self.width, self.height))

        pygame.display.set_caption("Fly-in")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "ressource", "background.jpg")
        self.background = self.load_background(path)
        self.clock = pygame.time.Clock()

    def load_background(self, path: str) -> Optional[pygame.Surface]:
        """Load and scale background image."""
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, (self.width, self.height))
        except FileNotFoundError:
            print(f"Background '{path}' not found, using default color")
            return None

    def draw_background(self) -> None:
        """Draw background image or fallback color."""
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((30, 30, 30))

    def run(self) -> None:
        """Main simulation loop."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.draw_background()
            self.draw_grid()
            self.draw_connections()
            self.draw_hubs()
            self.draw_hubs_name()
            self.draw_assets()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def draw_grid(self) -> None:
        """Draw radar-style grid over background."""
        radar_filter = pygame.Surface((self.width, self.height),
                                      pygame.SRCALPHA)
        radar_filter.fill((30, 30, 30, 200))
        self.screen.blit(radar_filter, (0, 0))

        for i in range(self.dif_x):
            x = i * self.cell_size
            pygame.draw.line(self.screen, (255, 255, 255),
                             (x, 0), (x, self.height))

        for j in range(self.dif_y):
            y = j * self.cell_size
            pygame.draw.line(self.screen, (255, 255, 255),
                             (0, y), (self.width, y))

        pygame.draw.line(self.screen, (255, 255, 255),
                         (self.width - 1, 0), (self.width - 1, self.height))
        pygame.draw.line(self.screen, (255, 255, 255),
                         (0, self.height - 1), (self.width, self.height - 1))

        pygame.draw.circle(self.screen, (255, 0, 0),
                           (self.origin_x, self.origin_y), 5)

    def draw_connections(self) -> None:
        """Draw lines between connected hubs."""
        for c in self.map.connections:
            mx = self.origin_x + c.zone1.x * self.cell_size
            my = self.origin_y + c.zone1.y * self.cell_size
            gx = self.origin_x + c.zone2.x * self.cell_size
            gy = self.origin_y + c.zone2.y * self.cell_size
            pygame.draw.line(self.screen, (163, 217, 207),
                             (mx, my), (gx, gy), 5)

    def draw_hubs(self) -> None:
        """Draw each hub as a colored circle."""
        for h in self.all_hubs:
            ox = self.origin_x + h.x * self.cell_size
            oy = self.origin_y + h.y * self.cell_size
            r = self.cell_size // 3
            color = self.color_hub(h)
            pygame.draw.circle(self.screen, color, (ox, oy), r)

    def color_hub(self, hub: Hub) -> tuple[int, int, int]:
        """Return RGB color for a hub based on its metadata color."""
        if hub.metadata.color == Color.rainbow:
            t = (pygame.time.get_ticks() / 2000) % 1.0
            r, g, b = colorsys.hsv_to_rgb(t, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))

        colors = {
            Color.red: (229, 138, 142),
            Color.blue: (138, 199, 129),
            Color.yellow: (229, 219, 138),
            Color.purple: (184, 143, 204),
            Color.green: (167, 204, 143),
            Color.orange: (229, 184, 138),
            Color.white: (255, 255, 255),
            Color.cyan: (163, 217, 207),
            Color.marron: (188, 143, 143),
            Color.darkred: (220, 100, 100),
            Color.black: (60, 60, 60),
            Color.gold: (255, 223, 100),
            Color.brown: (196, 164, 132),
            Color.crimson: (255, 120, 130),
            Color.violet: (210, 160, 255),
        }
        return colors[hub.metadata.color]

    def draw_hubs_name(self) -> None:
        """Draw hub names below each hub circle."""
        police = self.cell_size // 10
        font = pygame.font.SysFont("mono", police)
        for h in self.all_hubs:
            text = font.render(h.name, True, (255, 255, 255))
            dx = -text.get_width() // 2
            dy = self.cell_size // 3 + 3
            px = self.origin_x + h.x * self.cell_size
            py = self.origin_y + h.y * self.cell_size
            self.screen.blit(text, (px + dx, py + dy))

    def draw_assets(self) -> None:
        """Draw zone type icons on each hub."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        zone_icons = {
            Zone.normal: "normal",
            Zone.blocked: "blocked",
            Zone.restricted: "restricted",
            Zone.priority: "priority"
        }
        try:
            for h in self.all_hubs:
                mode = zone_icons[h.metadata.zone] + ".png"
                path = os.path.join(base_dir, "ressource", mode)
                s = self.cell_size // 3
                px = (self.origin_x + h.x * self.cell_size) - s // 2
                py = (self.origin_y + h.y * self.cell_size) - s // 2
                img = pygame.image.load(path).convert_alpha()
                asset = pygame.transform.scale(img, (s, s))
                self.screen.blit(asset, (px, py))
        except FileNotFoundError:
            raise FileNotFoundError("Asset zone type not found")
