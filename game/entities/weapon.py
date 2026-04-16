import pygame
import math
from game.constants import WEAPON_CONFIG, WEAPON_SINGLE, WEAPON_SPREAD, WEAPON_RAPID
from game.entities.bullet import Bullet


class Weapon:
    def __init__(self, weapon_type=WEAPON_SINGLE):
        self.set_type(weapon_type)
        self.last_shot = 0
        # Bonus stats from upgrades/gates
        self.bonus_damage = 0
        self.bonus_fire_rate = 0
        self.bonus_bullets = 0

    def set_type(self, weapon_type):
        self.weapon_type = weapon_type
        config = WEAPON_CONFIG[weapon_type]
        self.base_damage = config["damage"]
        self.base_fire_rate = config["fire_rate"]
        self.base_bullet_count = config["bullet_count"]
        self.spread_angle = config["spread_angle"]
        self.name = config["name"]
        self.color = config["color"]

    @property
    def damage(self):
        return max(1, self.base_damage + self.bonus_damage)

    @property
    def fire_rate(self):
        return max(50, self.base_fire_rate + self.bonus_fire_rate)

    @property
    def bullet_count(self):
        return max(1, self.base_bullet_count + self.bonus_bullets)

    def can_fire(self):
        now = pygame.time.get_ticks()
        return now - self.last_shot > self.fire_rate

    def fire(self, start_x, start_y, target, projectiles_group, all_sprites):
        if not self.can_fire():
            return False

        self.last_shot = pygame.time.get_ticks()
        count = self.bullet_count
        total_spread = self.spread_angle * (count - 1)
        start_angle = -total_spread / 2

        for i in range(count):
            angle_offset = start_angle + i * self.spread_angle if count > 1 else 0
            spread_x = target.rect.centerx + math.tan(math.radians(angle_offset)) * 200
            p = Bullet(
                start_x, start_y,
                spread_x, target.rect.centery,
                self.damage, self.color
            )
            projectiles_group.add(p)
            all_sprites.add(p)

        return True

    def get_power_rating(self):
        """Calculate a rough power rating for display."""
        dps = (self.damage * self.bullet_count) / (self.fire_rate / 1000.0)
        return int(dps)

    # ------------------------------------------------------------------
    # Spec method: draw
    # ------------------------------------------------------------------
    def draw(self, surface, x, y):
        """Draw a compact weapon badge (colored background + name) at (x, y)."""
        font = pygame.font.SysFont(None, 20)
        text = font.render(self.name, True, (255, 255, 255))
        badge_w = text.get_width() + 12
        badge_h = text.get_height() + 6
        badge = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        pygame.draw.rect(badge, (*self.color, 180), (0, 0, badge_w, badge_h), border_radius=4)
        pygame.draw.rect(badge, (255, 255, 255, 120), (0, 0, badge_w, badge_h), 1, border_radius=4)
        badge.blit(text, (6, 3))
        surface.blit(badge, (x, y))
