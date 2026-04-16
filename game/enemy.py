import pygame
import random
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, WHITE, BLACK, GREEN,
    ENEMY_SMALL, ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS,
    ENEMY_CONFIG
)
from game.character import Character


class Zombie(Character):
    def __init__(self, enemy_type=ENEMY_SMALL, speed_bonus=0, hp_bonus=0):
        config = ENEMY_CONFIG[enemy_type]
        super().__init__(
            hp=config["hp"] + int(hp_bonus),
            width=config["width"],
            height=config["height"],
        )
        self.enemy_type = enemy_type
        self.color = config["color"]
        self.gold_value = config["gold"]
        self.damage = config["damage"]
        self.is_elite = False

        self._draw_zombie()
        self.original_image = self.image.copy()

        self.flash_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.flash_image.fill(WHITE)
        self.hit_flash = 0

        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-80, -30)

        self.speed = config["speed"] + speed_bonus

        self.knockback_x = 0
        self.knockback_y = 0

    def _draw_zombie(self):
        """Draw a simple zombie sprite based on type."""
        w, h = self.width, self.height
        self.image.fill((0, 0, 0, 0))

        body_rect = pygame.Rect(w // 6, h // 3, w * 2 // 3, h * 2 // 3)
        pygame.draw.rect(self.image, self.color, body_rect)

        head_radius = w // 4
        pygame.draw.circle(self.image, self.color, (w // 2, h // 4), head_radius)

        eye_y = h // 4
        eye_offset = w // 8
        pygame.draw.circle(self.image, RED, (w // 2 - eye_offset, eye_y), 2)
        pygame.draw.circle(self.image, RED, (w // 2 + eye_offset, eye_y), 2)

    def set_elite(self):
        """Mark this enemy as elite — tougher with a glow."""
        self.is_elite = True
        self.max_health = int(self.max_health * 2.5)
        self.health = self.max_health
        self.gold_value = int(self.gold_value * 2)
        self._draw_zombie()
        w, h = self.width, self.height
        pygame.draw.rect(self.image, (255, 200, 50), (0, 0, w, h), 2)
        self.original_image = self.image.copy()

    def update(self):
        self.rect.y += self.speed

        if self.knockback_x != 0 or self.knockback_y != 0:
            self.rect.x += int(self.knockback_x)
            self.rect.y += int(self.knockback_y)
            self.knockback_x *= 0.8
            self.knockback_y *= 0.8
            if abs(self.knockback_x) < 0.5:
                self.knockback_x = 0
            if abs(self.knockback_y) < 0.5:
                self.knockback_y = 0

        if self.hit_flash > 0:
            self.hit_flash -= 1
            self.image = self.flash_image
        else:
            self.image = self.original_image

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()

    def draw_health_bar(self, surface, offset_x=0, offset_y=0):
        """Draw a health bar above the enemy."""
        if self.health >= self.max_health:
            return

        bar_width = self.width
        bar_height = 4
        x = self.rect.x + offset_x
        y = self.rect.y - 8 + offset_y

        pygame.draw.rect(surface, BLACK, (x - 1, y - 1, bar_width + 2, bar_height + 2))
        fill_width = int(bar_width * (self.health / self.max_health))
        color = GREEN if self.health > self.max_health * 0.5 else RED
        pygame.draw.rect(surface, color, (x, y, fill_width, bar_height))

    def apply_knockback(self, from_x, from_y, force=3):
        """Apply knockback away from a point."""
        dx = self.rect.centerx - from_x
        dy = self.rect.centery - from_y
        dist = max(1, (dx * dx + dy * dy) ** 0.5)
        self.knockback_x = (dx / dist) * force
        self.knockback_y = (dy / dist) * force


class Boss(Zombie):
    """Boss zombie — larger, tougher, with summon and warcry abilities."""

    def __init__(self, speed_bonus=0, hp_bonus=0):
        super().__init__(enemy_type=ENEMY_BOSS, speed_bonus=speed_bonus, hp_bonus=hp_bonus)
        self._draw_boss()
        self.original_image = self.image.copy()

        self.summon_cooldown = 0
        self.summon_interval = 180
        self.warcry_cooldown = 0
        self.warcry_interval = 300
        self.warcry_speed_buff = 1.5

    def _draw_boss(self):
        """Draw boss with scar marking."""
        self._draw_zombie()
        w, h = self.width, self.height
        pygame.draw.line(self.image, (0, 0, 0), (w // 3, h // 6), (w * 2 // 3, h // 3), 2)

    def summon(self, enemies_group, all_sprites_group):
        """Spawn smaller zombies around the boss."""
        if self.summon_cooldown > 0:
            return []

        self.summon_cooldown = self.summon_interval
        minions = []
        for offset_x in [-30, 30]:
            minion = Zombie(enemy_type=ENEMY_SMALL, speed_bonus=0.5)
            minion.rect.centerx = self.rect.centerx + offset_x
            minion.rect.centery = self.rect.centery
            minion.gold_value = 1
            enemies_group.add(minion)
            all_sprites_group.add(minion)
            minions.append(minion)
        return minions

    def warcry(self, enemies_group):
        """Buff nearby zombies with a speed boost."""
        if self.warcry_cooldown > 0:
            return

        self.warcry_cooldown = self.warcry_interval
        warcry_radius = 150
        for enemy in enemies_group:
            if enemy is self:
                continue
            dx = enemy.rect.centerx - self.rect.centerx
            dy = enemy.rect.centery - self.rect.centery
            dist_sq = dx * dx + dy * dy
            if dist_sq < warcry_radius * warcry_radius:
                enemy.speed *= self.warcry_speed_buff

    def update(self, enemies_group=None, all_sprites_group=None):
        super().update()
        if self.summon_cooldown > 0:
            self.summon_cooldown -= 1
        elif enemies_group is not None and all_sprites_group is not None:
            self.summon(enemies_group, all_sprites_group)

        if self.warcry_cooldown > 0:
            self.warcry_cooldown -= 1
        elif enemies_group is not None:
            self.warcry(enemies_group)
