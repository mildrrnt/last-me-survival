import pygame
import random
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, RED, WHITE, BLACK, GREEN,
    ENEMY_SMALL, ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS,
    ENEMY_CHARGER, ENEMY_SPLITTER,
    ENEMY_CONFIG
)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type=ENEMY_SMALL, speed_bonus=0, hp_bonus=0):
        super().__init__()
        config = ENEMY_CONFIG[enemy_type]
        self.enemy_type = enemy_type
        self.width = config["width"]
        self.height = config["height"]
        self.color = config["color"]
        self.gold_value = config["gold"]
        self.is_elite = False

        # Build sprite
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_zombie()
        self.original_image = self.image.copy()

        # Flash image
        self.flash_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.flash_image.fill(WHITE)
        self.hit_flash = 0

        self.rect = self.image.get_rect()

        # Spawn randomly at top
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-80, -30)

        self.speed = config["speed"] + speed_bonus
        self.max_health = config["hp"] + int(hp_bonus)
        self.health = self.max_health

        # Knockback
        self.knockback_x = 0
        self.knockback_y = 0

    def _draw_zombie(self):
        """Draw a simple zombie sprite based on type."""
        w, h = self.width, self.height
        self.image.fill((0, 0, 0, 0))

        # Body
        body_rect = pygame.Rect(w // 6, h // 3, w * 2 // 3, h * 2 // 3)
        pygame.draw.rect(self.image, self.color, body_rect)

        # Head
        head_radius = w // 4
        pygame.draw.circle(self.image, self.color, (w // 2, h // 4), head_radius)

        # Eyes (red dots)
        eye_y = h // 4
        eye_offset = w // 8
        pygame.draw.circle(self.image, RED, (w // 2 - eye_offset, eye_y), 2)
        pygame.draw.circle(self.image, RED, (w // 2 + eye_offset, eye_y), 2)

        # Boss gets a scar or marking
        if self.enemy_type == ENEMY_BOSS:
            pygame.draw.line(self.image, BLACK, (w // 3, h // 6), (w * 2 // 3, h // 3), 2)

    def set_elite(self):
        """Mark this enemy as elite — tougher with a glow."""
        self.is_elite = True
        self.max_health = int(self.max_health * 2.5)
        self.health = self.max_health
        self.gold_value = int(self.gold_value * 2)
        # Redraw with gold border glow
        self._draw_zombie()
        w, h = self.width, self.height
        pygame.draw.rect(self.image, (255, 200, 50), (0, 0, w, h), 2)
        self.original_image = self.image.copy()

    def update(self):
        self.rect.y += self.speed

        # Apply knockback
        if self.knockback_x != 0 or self.knockback_y != 0:
            self.rect.x += int(self.knockback_x)
            self.rect.y += int(self.knockback_y)
            self.knockback_x *= 0.8
            self.knockback_y *= 0.8
            if abs(self.knockback_x) < 0.5:
                self.knockback_x = 0
            if abs(self.knockback_y) < 0.5:
                self.knockback_y = 0

        # Hit flash
        if self.hit_flash > 0:
            self.hit_flash -= 1
            self.image = self.flash_image
        else:
            self.image = self.original_image

        # Keep within horizontal bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # Kill if off screen bottom
        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()

    def draw_health_bar(self, surface, offset_x=0, offset_y=0):
        """Draw a health bar above the enemy."""
        if self.health >= self.max_health:
            return  # Don't show for full health

        bar_width = self.width
        bar_height = 4
        x = self.rect.x + offset_x
        y = self.rect.y - 8 + offset_y

        # Background
        pygame.draw.rect(surface, BLACK, (x - 1, y - 1, bar_width + 2, bar_height + 2))
        # Health fill
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


class ChargerEnemy(Enemy):
    """Approaches to mid-screen, pauses and vibrates, then rushes at player."""

    STATE_APPROACH = 0
    STATE_PAUSE = 1
    STATE_CHARGE = 2

    def __init__(self, speed_bonus=0, hp_bonus=0, player_ref=None):
        super().__init__(enemy_type=ENEMY_CHARGER, speed_bonus=speed_bonus, hp_bonus=hp_bonus)
        self.charge_state = self.STATE_APPROACH
        self.pause_timer = 0
        self.pause_duration = 45  # frames (~0.75s)
        self.charge_speed = self.speed * 2.5
        self.player_ref = player_ref
        self.vibrate_offset = 0
        self.charge_target_x = SCREEN_WIDTH // 2

        # Redraw with charger look (pointed head)
        self._draw_charger()
        self.original_image = self.image.copy()

    def _draw_charger(self):
        w, h = self.width, self.height
        self.image.fill((0, 0, 0, 0))
        # Pointed body
        points = [(w // 2, 0), (w, h), (0, h)]
        pygame.draw.polygon(self.image, self.color, points)
        # Eyes
        eye_y = h // 2
        pygame.draw.circle(self.image, RED, (w // 3, eye_y), 2)
        pygame.draw.circle(self.image, RED, (w * 2 // 3, eye_y), 2)

    def update(self):
        if self.charge_state == self.STATE_APPROACH:
            # Move down to mid-screen area
            self.rect.y += self.speed
            if self.rect.y >= SCREEN_HEIGHT * 0.35:
                self.charge_state = self.STATE_PAUSE
                self.pause_timer = self.pause_duration
                # Lock target on player
                if self.player_ref and self.player_ref.rect:
                    self.charge_target_x = self.player_ref.rect.centerx

        elif self.charge_state == self.STATE_PAUSE:
            # Vibrate in place
            self.pause_timer -= 1
            self.vibrate_offset = random.randint(-2, 2)
            self.rect.x += self.vibrate_offset
            if self.pause_timer <= 0:
                self.charge_state = self.STATE_CHARGE

        elif self.charge_state == self.STATE_CHARGE:
            # Rush toward where player was
            dx = self.charge_target_x - self.rect.centerx
            dist = abs(dx)
            if dist > 2:
                self.rect.x += int((dx / dist) * self.charge_speed * 0.3)
            self.rect.y += self.charge_speed

        # Apply knockback
        if self.knockback_x != 0 or self.knockback_y != 0:
            self.rect.x += int(self.knockback_x)
            self.rect.y += int(self.knockback_y)
            self.knockback_x *= 0.8
            self.knockback_y *= 0.8
            if abs(self.knockback_x) < 0.5:
                self.knockback_x = 0
            if abs(self.knockback_y) < 0.5:
                self.knockback_y = 0

        # Hit flash
        if self.hit_flash > 0:
            self.hit_flash -= 1
            self.image = self.flash_image
        else:
            self.image = self.original_image

        # Bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        if self.rect.top > SCREEN_HEIGHT + 20:
            self.kill()


class SplitterEnemy(Enemy):
    """When killed, splits into 2 small fast enemies."""

    def __init__(self, speed_bonus=0, hp_bonus=0):
        super().__init__(enemy_type=ENEMY_SPLITTER, speed_bonus=speed_bonus, hp_bonus=hp_bonus)
        self.has_split = False

        # Redraw with splitter look (rounder with split line)
        self._draw_splitter()
        self.original_image = self.image.copy()

    def _draw_splitter(self):
        w, h = self.width, self.height
        self.image.fill((0, 0, 0, 0))
        # Round body
        pygame.draw.ellipse(self.image, self.color, (2, 2, w - 4, h - 4))
        # Split line down center
        pygame.draw.line(self.image, (200, 255, 220), (w // 2, 4), (w // 2, h - 4), 1)
        # Eyes
        eye_y = h // 3
        pygame.draw.circle(self.image, RED, (w // 3, eye_y), 2)
        pygame.draw.circle(self.image, RED, (w * 2 // 3, eye_y), 2)

    def spawn_children(self):
        """Return two small fast enemies at this position."""
        children = []
        for offset in [-12, 12]:
            child = Enemy(
                enemy_type=ENEMY_SMALL,
                speed_bonus=1.5,
                hp_bonus=0
            )
            child.rect.centerx = self.rect.centerx + offset
            child.rect.centery = self.rect.centery
            child.gold_value = 1
            children.append(child)
        self.has_split = True
        return children
