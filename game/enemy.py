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
        self.gold_value = config["gold"]
        self.damage = config["damage"]
        self.is_elite = False

        # Animation state
        self.current_state = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 6  # game-frames per animation-frame (10 FPS at 60 FPS)
        self.dying = False

        # Load sprite sheet animations
        self._setup_animations()
        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect()

        # Flash image
        self.flash_image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.flash_image.fill(WHITE)
        self.hit_flash = 0

        # Spawn randomly at top
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-80, -30)

        self.speed = config["speed"] + speed_bonus

        # Knockback
        self.knockback_x = 0
        self.knockback_y = 0

    def _extract_frames_strip(self, filepath, num_frames=None):
        """Load a horizontal strip image and slice it into frames."""
        strip = pygame.image.load(filepath).convert_alpha()
        frame_h = strip.get_height()
        if num_frames is None:
            num_frames = max(1, strip.get_width() // frame_h)
        frame_w = strip.get_width() // num_frames
        frames = []
        for col in range(num_frames):
            rect = pygame.Rect(col * frame_w, 0, frame_w, frame_h)
            frame = strip.subsurface(rect).copy()
            if (frame_w, frame_h) != (self.width, self.height):
                frame = pygame.transform.scale(frame, (self.width, self.height))
            frames.append(frame)
        return frames

    def _setup_animations(self):
        config = ENEMY_CONFIG[self.enemy_type]
        self.animations = {}
        for name, info in config["animations"].items():
            self.animations[name] = self._extract_frames_strip(
                info["file"], info.get("frames")
            )

    def set_animation_state(self, state):
        """Switch to a new animation. Resets frame to 0."""
        if state == self.current_state:
            return
        if state not in self.animations:
            return
        self.current_state = state
        self.frame_index = 0
        self.frame_timer = 0

    def set_elite(self):
        """Mark this enemy as elite — tougher with a glow."""
        self.is_elite = True
        self.max_health = int(self.max_health * 2.5)
        self.health = self.max_health
        self.gold_value = int(self.gold_value * 2)
        # Add gold border glow to every animation frame
        for anim_name, frames in self.animations.items():
            for i, frame in enumerate(frames):
                tinted = frame.copy()
                w, h = tinted.get_size()
                pygame.draw.rect(tinted, (255, 200, 50), (0, 0, w, h), 2)
                frames[i] = tinted

    def update(self):
        # Skip movement when dying
        if not self.dying:
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

        # Advance animation frame
        self.frame_timer += 1
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.frame_index += 1

            frames = self.animations[self.current_state]
            if self.frame_index >= len(frames):
                if self.current_state == "die":
                    self.kill()
                    return
                elif self.current_state == "hurt":
                    self.set_animation_state("idle")
                else:
                    self.frame_index = 0

        # Apply current frame (with flash override)
        current_frame = self.animations[self.current_state][self.frame_index]
        if self.hit_flash > 0:
            self.hit_flash -= 1
            self.image = current_frame.copy()
            self.image.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            self.image = current_frame

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


class Boss(Zombie):
    """Boss zombie — larger, tougher, with summon and warcry abilities."""

    def __init__(self, speed_bonus=0, hp_bonus=0):
        super().__init__(enemy_type=ENEMY_BOSS, speed_bonus=speed_bonus, hp_bonus=hp_bonus)

        # Summon cooldown (frames)
        self.summon_cooldown = 0
        self.summon_interval = 180  # ~3 seconds at 60 FPS

        # Warcry cooldown (frames)
        self.warcry_cooldown = 0
        self.warcry_interval = 300  # ~5 seconds at 60 FPS
        self.warcry_speed_buff = 1.5

    def summon(self, enemies_group, all_sprites_group):
        """Spawn smaller zombies around the boss."""
        if self.summon_cooldown > 0:
            return []

        self.summon_cooldown = self.summon_interval
        minions = []
        for offset_x in [-30, 30]:
            minion = Zombie(
                enemy_type=ENEMY_SMALL,
                speed_bonus=0.5,
                hp_bonus=0,
            )
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
