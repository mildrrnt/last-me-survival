import pygame
import math
import random
from game.constants import (
    SCREEN_HEIGHT,
    POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST,
    POWERUP_COLORS, POWERUP_LABELS, POWERUP_DURATIONS
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

        # Spec attributes: duration (active effect length) and value (effect magnitude)
        self.duration = POWERUP_DURATIONS[powerup_type]
        _effect_values = {
            POWERUP_RAPID_FIRE:   200,  # ms subtracted from fire_rate
            POWERUP_SHIELD:         1,  # blocks one hit
            POWERUP_DAMAGE_BOOST:  15,  # bonus damage added
        }
        self.value = _effect_values.get(powerup_type, 0)

        # Storage for pre-activation weapon stats (set in activate())
        self._original_fire_rate = None
        self._original_damage = None

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

    # ------------------------------------------------------------------
    # Spec method: activate
    # ------------------------------------------------------------------
    def activate(self, player, game_manager):
        """Apply this powerup's effect to player and register the active timer."""
        if self.powerup_type == POWERUP_RAPID_FIRE:
            if self.powerup_type not in game_manager.active_powerups:
                # First activation — snapshot current bonus
                self._original_fire_rate = player.weapon.bonus_fire_rate
            else:
                # Already active — inherit original so the effect does not stack
                prev = game_manager._active_powerup_instances.get(self.powerup_type)
                self._original_fire_rate = (
                    prev._original_fire_rate if prev else player.weapon.bonus_fire_rate
                )
            player.weapon.bonus_fire_rate = self._original_fire_rate - self.value

        elif self.powerup_type == POWERUP_SHIELD:
            pass  # Shield is checked per-frame in GameManager.check_collisions

        elif self.powerup_type == POWERUP_DAMAGE_BOOST:
            if self.powerup_type not in game_manager.active_powerups:
                self._original_damage = player.weapon.bonus_damage
            else:
                prev = game_manager._active_powerup_instances.get(self.powerup_type)
                self._original_damage = (
                    prev._original_damage if prev else player.weapon.bonus_damage
                )
            player.weapon.bonus_damage = self._original_damage + self.value

        game_manager.active_powerups[self.powerup_type] = self.duration
        game_manager._active_powerup_instances[self.powerup_type] = self

    # ------------------------------------------------------------------
    # Spec method: deactivate
    # ------------------------------------------------------------------
    def deactivate(self, player):
        """Restore player stats to their pre-activation values."""
        if self.powerup_type == POWERUP_RAPID_FIRE and self._original_fire_rate is not None:
            player.weapon.bonus_fire_rate = self._original_fire_rate
        elif self.powerup_type == POWERUP_DAMAGE_BOOST and self._original_damage is not None:
            player.weapon.bonus_damage = self._original_damage

    # ------------------------------------------------------------------
    # Spec method: collide
    # ------------------------------------------------------------------
    def collide(self, player, game_manager):
        """Activate effect, trigger visual feedback, and remove this pickup."""
        self.activate(player, game_manager)
        game_manager.ui_manager.add_effect_text(
            player.rect.centerx, player.rect.top - 20,
            self.label, True
        )
        game_manager.particle_manager.spawn_explosion(
            player.rect.centerx, player.rect.centery,
            count=12, color=self.color
        )
        self.kill()
