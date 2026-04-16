import pygame
import math
import random
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    GEM_GREEN, GEM_MAGNET_RADIUS, GEM_MAGNET_SPEED, GEM_DRIFT_SPEED
)


class XPGem(pygame.sprite.Sprite):
    def __init__(self, x, y, xp_value=1):
        super().__init__()
        self.xp_value = xp_value
        self.base_x = float(x)
        self.base_y = float(y)

        # Size based on XP value
        if xp_value >= 25:
            self.radius = 8
        elif xp_value >= 5:
            self.radius = 6
        elif xp_value >= 3:
            self.radius = 5
        else:
            self.radius = 4

        self.size = self.radius * 2 + 4
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        # Animation
        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.drift_vx = random.uniform(-0.3, 0.3)
        self.being_pulled = False
        self.lifetime = 600  # 10 seconds at 60fps

    def update(self, player_rect=None):
        self.pulse_timer += 0.12
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        # Drift downward and slightly sideways
        self.base_y += GEM_DRIFT_SPEED
        self.base_x += self.drift_vx

        # Magnetic pull toward player
        if player_rect is not None:
            dx = player_rect.centerx - self.base_x
            dy = player_rect.centery - self.base_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < GEM_MAGNET_RADIUS and dist > 0:
                self.being_pulled = True
                pull_strength = GEM_MAGNET_SPEED * (1 - dist / GEM_MAGNET_RADIUS)
                self.base_x += (dx / dist) * pull_strength
                self.base_y += (dy / dist) * pull_strength
            else:
                self.being_pulled = False

        self.rect.center = (int(self.base_x), int(self.base_y))

        # Remove if off screen
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()
            return

        # Redraw with pulse
        self._draw()

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        cx, cy = self.size // 2, self.size // 2
        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)

        # Outer glow
        glow_radius = int(self.radius * 1.5 * pulse)
        glow_color = (0, 230, 64, 60)
        pygame.draw.circle(self.image, glow_color, (cx, cy), glow_radius)

        # Core gem
        core_radius = int(self.radius * pulse)
        pygame.draw.circle(self.image, GEM_GREEN, (cx, cy), core_radius)

        # Bright center
        inner_radius = max(1, core_radius // 2)
        bright = (150, 255, 180)
        pygame.draw.circle(self.image, bright, (cx, cy), inner_radius)

        # Fade when about to expire
        if self.lifetime < 60:
            alpha = int(255 * (self.lifetime / 60))
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
