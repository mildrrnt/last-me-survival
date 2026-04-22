import pygame
import math
from game.constants import WEAPON_CONFIG, WEAPON_SINGLE
from game.bullet import Bullet


class Weapon:
    """Handles firing logic and tracks weapon stats."""

    def __init__(self, weapon_type=WEAPON_SINGLE):
        self.set_type(weapon_type)
        self.last_shot = 0
        self.bonus_damage = 0
        self.bonus_fire_rate = 0
        self.bonus_bullets = 0

    def set_type(self, weapon_type):
        self.weapon_type = weapon_type
        config = WEAPON_CONFIG[weapon_type]
        self._base_damage = config["damage"]
        self._base_fire_rate = config["fire_rate"]
        self._base_bullet_count = config["bullet_count"]
        self.spread_angle = config["spread_angle"]
        self.name = config["name"]
        self.color = config["color"]

    @property
    def damage(self):
        return max(1, self._base_damage + self.bonus_damage)

    @property
    def fireRate(self):
        return max(50, self._base_fire_rate + self.bonus_fire_rate)

    @property
    def numBullet(self):
        return max(1, self._base_bullet_count + self.bonus_bullets)

    def can_fire(self):
        now = pygame.time.get_ticks()
        return now - self.last_shot > self.fireRate

    def fire(self, start_x, start_y, target, projectiles_group, all_sprites):
        if not self.can_fire():
            return False

        self.last_shot = pygame.time.get_ticks()
        count = self.numBullet
        total_spread = self.spread_angle * (count - 1)
        start_angle = -total_spread / 2

        target_x = target.rect.centerx if target else start_x
        target_y = target.rect.centery if target else start_y - 200

        for i in range(count):
            angle_offset = start_angle + i * self.spread_angle if count > 1 else 0
            spread_x = target_x + math.tan(math.radians(angle_offset)) * 200
            p = Bullet(
                start_x, start_y,
                spread_x, target_y,
                self.damage, self.color
            )
            projectiles_group.add(p)
            all_sprites.add(p)

        return True

    def get_power_rating(self):
        """Calculate a rough power rating for display."""
        dps = (self.damage * self.numBullet) / (self.fireRate / 1000.0)
        return int(dps)

    def draw(self, surface, x, y):
        """Draw a compact weapon badge at (x, y)."""
        font = pygame.font.SysFont(None, 20)
        text = font.render(self.name, True, (255, 255, 255))
        badge_w = text.get_width() + 12
        badge_h = text.get_height() + 6
        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*self.color, 180), (0, 0, badge_w, badge_h), border_radius=4)
        pygame.draw.rect(badge, (255, 255, 255, 120), (0, 0, badge_w, badge_h), 1, border_radius=4)
        badge.blit(text, (6, 3))
        surface.blit(badge, (x, y))
