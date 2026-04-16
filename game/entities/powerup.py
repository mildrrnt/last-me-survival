import pygame
import math
import random
from game.constants import (
    SCREEN_HEIGHT,
    POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST,
    POWERUP_COLORS, POWERUP_LABELS
)


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, powerup_type=POWERUP_RAPID_FIRE):
        super().__init__()
        self.powerup_type = powerup_type
        self.color = POWERUP_COLORS[powerup_type]
        self.label = POWERUP_LABELS[powerup_type]
        self.base_x = float(x)
        self.base_y = float(y)

        self.size = 22
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        self.pulse_timer = random.uniform(0, math.pi * 2)
        self.drift_speed = 0.5
        self.lifetime = 480  # 8 seconds at 60fps

        # Icon symbols
        self.icon_map = {
            POWERUP_RAPID_FIRE: "R",
            POWERUP_SHIELD: "S",
            POWERUP_DAMAGE_BOOST: "D",
        }

    def update(self):
        self.pulse_timer += 0.1
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()
            return

        self.base_y += self.drift_speed
        self.rect.center = (int(self.base_x), int(self.base_y))

        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()
            return

        self._draw()

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        cx, cy = self.size // 2, self.size // 2
        pulse = 0.8 + 0.2 * math.sin(self.pulse_timer)

        # Outer glow
        glow_r = int(10 * pulse)
        glow_color = (*self.color, 80)
        pygame.draw.circle(self.image, glow_color, (cx, cy), glow_r)

        # Core circle
        core_r = int(8 * pulse)
        pygame.draw.circle(self.image, self.color, (cx, cy), core_r)

        # Border
        pygame.draw.circle(self.image, (255, 255, 255), (cx, cy), core_r, 1)

        # Letter icon
        font = pygame.font.SysFont(None, 16)
        icon = font.render(self.icon_map.get(self.powerup_type, "?"), True, (255, 255, 255))
        self.image.blit(icon, (cx - icon.get_width() // 2, cy - icon.get_height() // 2))

        # Fade when expiring
        if self.lifetime < 60:
            alpha = int(255 * (self.lifetime / 60))
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)
