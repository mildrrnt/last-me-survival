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

		# Spec attributes
		self.type = powerup_type
		self.duration = POWERUP_DURATIONS[powerup_type]
		_effect_values = {
			POWERUP_RAPID_FIRE:   200,
			POWERUP_SHIELD:         1,
			POWERUP_DAMAGE_BOOST:  15,
		}
		self.value = _effect_values.get(powerup_type, 0)

		self.color = POWERUP_COLORS[powerup_type]
		self.label = POWERUP_LABELS[powerup_type]
		self.base_x = float(x)
		self.base_y = float(y)

		self.size = 22
		self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
		self.rect = self.image.get_rect(center=(int(x), int(y)))

		self.pulse_timer = random.uniform(0, math.pi * 2)
		self.drift_speed = 0.5
		self.lifetime = 480

		self._original_fire_rate = None
		self._original_damage = None

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

		glow_r = int(10 * pulse)
		pygame.draw.circle(self.image, (*self.color, 80), (cx, cy), glow_r)

		core_r = int(8 * pulse)
		pygame.draw.circle(self.image, self.color, (cx, cy), core_r)
		pygame.draw.circle(self.image, (255, 255, 255), (cx, cy), core_r, 1)

		font = pygame.font.SysFont(None, 16)
		icon = font.render(self.icon_map.get(self.type, "?"), True, (255, 255, 255))
		self.image.blit(icon, (cx - icon.get_width() // 2, cy - icon.get_height() // 2))

		if self.lifetime < 60:
			self.image.set_alpha(int(255 * (self.lifetime / 60)))
		else:
			self.image.set_alpha(255)

	def activate(self, player, game):
		"""Apply this powerup's effect to player and register the active timer."""
		if self.type == POWERUP_RAPID_FIRE:
			if self.type not in game.active_powerups:
				self._original_fire_rate = player.weapon.bonus_fire_rate
			else:
				prev = game._active_powerup_instances.get(self.type)
				self._original_fire_rate = (
					prev._original_fire_rate if prev else player.weapon.bonus_fire_rate
				)
			player.weapon.bonus_fire_rate = self._original_fire_rate - self.value

		elif self.type == POWERUP_SHIELD:
			pass  # Shield is checked per-frame in Game.check_collisions

		elif self.type == POWERUP_DAMAGE_BOOST:
			if self.type not in game.active_powerups:
				self._original_damage = player.weapon.bonus_damage
			else:
				prev = game._active_powerup_instances.get(self.type)
				self._original_damage = (
					prev._original_damage if prev else player.weapon.bonus_damage
				)
			player.weapon.bonus_damage = self._original_damage + self.value

		game.active_powerups[self.type] = self.duration
		game._active_powerup_instances[self.type] = self

	def deactivate(self, player):
		"""Restore player stats to their pre-activation values."""
		if self.type == POWERUP_RAPID_FIRE and self._original_fire_rate is not None:
			player.weapon.bonus_fire_rate = self._original_fire_rate
		elif self.type == POWERUP_DAMAGE_BOOST and self._original_damage is not None:
			player.weapon.bonus_damage = self._original_damage

	def collide(self, player, game):
		"""Activate effect, trigger visual feedback, and remove this pickup."""
		self.activate(player, game)
		game.add_effect_text(player.rect.centerx, player.rect.top - 20, self.label, True)
		game.spawn_explosion(player.rect.centerx, player.rect.centery, count=12, color=self.color)
		self.kill()
