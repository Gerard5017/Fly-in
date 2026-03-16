import os
import pygame
from .map_validator import MapValidator
from .simulation import Simulation
from .hub import Hub
from .drone import Drone
from typing import Optional
from .metadata import Color, Zone
import colorsys

ANIM_DURATION_MS = 1000


class Visualiser():
    """Pygame-based visualizer for the drone simulation.

    Renders the map graph, hub states, drone positions, and a HUD panel
    on each frame. Supports step-by-step navigation with arrow keys.
    Drone movements are smoothly interpolated over ANIM_DURATION_MS
    milliseconds.

    Attributes:
        map: The validated map being visualized.
        all_hubs: All hubs including start and end.
        simulation: The simulation instance driving drone movement.
        cell_size: Pixel size of one grid cell.
        origin_x: Pixel x-offset for the coordinate origin.
        origin_y: Pixel y-offset for the coordinate origin.
        width: Window width in pixels.
        height: Window height in pixels.
        screen: The pygame display surface.
        background: Optional pre-loaded background image.
        clock: Pygame clock used to cap the frame rate.
        anim_progress: Current animation interpolation factor (0.0-1.0).
        anim_start_ms: Timestamp in ms when the current animation started.
        drone_src: Pixel (x, y) start positions per drone for animation.
        drone_dst: Pixel (x, y) end positions per drone for animation.
        animating: Whether an animation is currently in progress.
    """

    def __init__(self, map: MapValidator) -> None:
        """Initialize the visualizer window and simulation.

        Computes grid dimensions from hub coordinates, creates the pygame
        window, and prepares the simulation with drone paths.

        Args:
            map: A validated MapValidator instance to render.
        """
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
        pygame.init()

        self.map = map
        self.all_hubs: list[Hub] = self.map.hub[:]
        if self.map.start_hub is not None:
            self.all_hubs.append(self.map.start_hub)
        if self.map.end_hub is not None:
            self.all_hubs.append(self.map.end_hub)

        self.simulation = Simulation(self.all_hubs, self.map)
        self.simulation.create_drone()

        max_x = max(h.x for h in self.all_hubs)
        max_y = max(h.y for h in self.all_hubs)
        min_x = min(h.x for h in self.all_hubs)
        min_y = min(h.y for h in self.all_hubs)

        self.dif_x = max_x - min_x + 2
        self.dif_y = max_y - min_y + 2

        self.cell_size = min(1800 // self.dif_x, 900 // self.dif_y)
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

        self.animating: bool = False
        self.anim_progress: float = 1.0
        self.anim_start_ms: int = 0
        self.drone_src: dict[str, tuple[float, float]] = {}
        self.drone_dst: dict[str, tuple[float, float]] = {}

        self._snapshot_drone_positions()

    def _hub_pixel(self, hub: Hub) -> tuple[float, float]:
        """Return the pixel center coordinates of a hub.

        Args:
            hub: The hub to locate on screen.

        Returns:
            A (px, py) tuple of float pixel coordinates.
        """
        return (
            float(self.origin_x + hub.x * self.cell_size),
            float(self.origin_y + hub.y * self.cell_size),
        )

    def _snapshot_drone_positions(self) -> None:
        """Record the current pixel position of every drone as their source.

        Called before exec_turn so that drone_src holds the pre-move
        positions and drone_dst will be populated after the move.
        """
        for drone in self.simulation.drones:
            pos = self._hub_pixel(drone.current_zone())
            self.drone_src[drone.drone_id] = pos
            self.drone_dst[drone.drone_id] = pos

    def _start_animation(self) -> None:
        """Capture post-move positions and start the animation timer.

        Must be called immediately after exec_turn(True) so that
        drone_dst reflects where each drone moved to.
        """
        for drone in self.simulation.drones:
            self.drone_dst[drone.drone_id] = self._hub_pixel(
                drone.current_zone()
            )
        self.anim_start_ms = pygame.time.get_ticks()
        self.anim_progress = 0.0
        self.animating = True

    def _update_animation(self) -> None:
        """Advance the animation progress based on elapsed time.

        Sets animating to False once the animation has completed.
        """
        elapsed = pygame.time.get_ticks() - self.anim_start_ms
        self.anim_progress = min(elapsed / ANIM_DURATION_MS, 1.0)
        if self.anim_progress >= 1.0:
            self.animating = False
            self._snapshot_drone_positions()

    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linearly interpolate between two float values.

        Args:
            a: Start value.
            b: End value.
            t: Interpolation factor in the range [0.0, 1.0].

        Returns:
            The interpolated value between a and b.
        """
        return a + (b - a) * t

    def _ease(self, t: float) -> float:
        """Apply a smooth-step easing function to a linear factor.

        Uses the cubic smoothstep formula: 3t^2 - 2t^3.

        Args:
            t: Linear interpolation factor in the range [0.0, 1.0].

        Returns:
            Eased interpolation factor in the range [0.0, 1.0].
        """
        return t * t * (3.0 - 2.0 * t)

    def _drone_pixel(self, drone: Drone) -> tuple[float, float]:
        """Return the current interpolated pixel position of a drone.

        Args:
            drone: The drone whose position is needed.

        Returns:
            A (px, py) tuple of interpolated pixel coordinates.
        """
        src = self.drone_src.get(drone.drone_id,
                                 self._hub_pixel(drone.current_zone()))
        dst = self.drone_dst.get(drone.drone_id,
                                 self._hub_pixel(drone.current_zone()))
        t = self._ease(self.anim_progress)
        return (
            self._lerp(src[0], dst[0], t),
            self._lerp(src[1], dst[1], t),
        )

    def load_background(self, path: str) -> Optional[pygame.Surface]:
        """Load and scale a background image to fit the window.

        Args:
            path: Absolute path to the background image file.

        Returns:
            A scaled pygame Surface, or None if the file is not found.
        """
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, (self.width, self.height))
        except FileNotFoundError:
            print(f"Background '{path}' not found, using default color")
            return None

    def draw_background(self) -> None:
        """Draw the background image or a solid fallback color."""
        if self.background is not None:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((30, 30, 30))

    def run(self) -> None:
        """Start the main event and render loop.

        Handles keyboard events:
            - Right arrow: advance one turn and trigger animation.
            - Left arrow / Escape: undo one turn or close the window.

        Inputs are ignored while an animation is in progress.
        Runs until the window is closed.
        """
        running = True
        while running:
            if self.animating:
                self._update_animation()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and not self.animating:
                    if event.key == pygame.K_RIGHT:
                        self._snapshot_drone_positions()
                        self.simulation.exec_turn(True)
                        self._start_animation()
                    if event.key == pygame.K_LEFT:
                        self.simulation.exec_turn(False)
                        self._snapshot_drone_positions()
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.draw_background()
            self.draw_grid()
            self.draw_connections()
            self.draw_hubs()
            self.draw_hubs_name()
            self.draw_assets()
            self.draw_drones()
            self.draw_drones_names()
            self.draw_pannel()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def draw_grid(self) -> None:
        """Draw a semi-transparent radar-style grid over the background."""
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
        """Draw lines between all connected hub pairs."""
        for c in self.map.connections:
            mx = self.origin_x + c.zone1.x * self.cell_size
            my = self.origin_y + c.zone1.y * self.cell_size
            gx = self.origin_x + c.zone2.x * self.cell_size
            gy = self.origin_y + c.zone2.y * self.cell_size
            pygame.draw.line(self.screen, (163, 217, 207),
                             (mx, my), (gx, gy), 5)

    def draw_hubs(self) -> None:
        """Draw each hub as a colored circle at its grid position."""
        for h in self.all_hubs:
            ox = self.origin_x + h.x * self.cell_size
            oy = self.origin_y + h.y * self.cell_size
            r = self.cell_size // 3
            color = self.color_hub(h)
            pygame.draw.circle(self.screen, color, (ox, oy), r)

    def color_hub(self, hub: Hub) -> tuple[int, int, int]:
        """Return the RGB color for a hub based on its metadata color.

        Rainbow hubs cycle through hues over time using HSV conversion.

        Args:
            hub: The hub whose color is needed.

        Returns:
            An (R, G, B) tuple with values in the range 0-255.
        """
        if hub.metadata.color == Color.rainbow:
            t = (pygame.time.get_ticks() / 2000) % 1.0
            r, g, b = colorsys.hsv_to_rgb(t, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))

        colors: dict[Color, tuple[int, int, int]] = {
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
        """Draw each hub's name as small text below its circle."""
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
        """Draw zone-type icons on top of each hub circle.

        Raises:
            FileNotFoundError: If any zone icon image file is missing.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        zone_icons: dict[Zone, str] = {
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

    def draw_drones(self) -> None:
        """Draw each drone sprite at its current interpolated position.

        Uses drone_src and drone_dst with anim_progress to smoothly
        move sprites between hub positions during animation.

        Raises:
            FileNotFoundError: If the drone sprite image file is missing.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "ressource", "drone.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            s = self.cell_size // 2
            asset = pygame.transform.scale(img, (s, s))
            for drone in self.simulation.drones:
                cx, cy = self._drone_pixel(drone)
                px = int(cx) - s // 2
                py = int(cy) - s // 2
                self.screen.blit(asset, (px, py))
        except FileNotFoundError:
            raise FileNotFoundError("Asset zone type not found")

    def draw_drones_names(self) -> None:
        """Draw each drone's ID label centered on its sprite."""
        s = self.cell_size // 2
        police = s // 6
        font = pygame.font.SysFont("mono", police)
        for d in self.simulation.drones:
            cx, cy = self._drone_pixel(d)
            text = font.render(d.drone_id, True, (255, 255, 255))
            px = int(cx) - text.get_width() // 2
            py = int(cy) - text.get_height() // 2
            self.screen.blit(text, (px, py))

    def draw_pannel(self) -> None:
        """Draw the HUD info panel in the bottom-right corner.

        Displays the current turn number and keyboard controls on a
        semi-transparent dark background.
        """
        font = pygame.font.SysFont("mono", 18)
        padding = 10
        lines = [
            f"Turn: {self.simulation.turn}",
            "-" * 20,
            "esc: close window",
            "->:  next turn",
            "<-:  previous turn",
        ]
        line_height = 18 + padding
        panel_h = line_height * len(lines) + padding * 2
        panel_w = max(font.size(ln)[0] for ln in lines) + padding * 2
        px = self.width - panel_w - padding
        py = self.height - panel_h - padding
        surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 180))
        self.screen.blit(surface, (px, py))
        for i, line in enumerate(lines):
            text = font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (px + padding,
                                    py + padding + i * line_height))
