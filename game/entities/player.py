import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLUE, DARK_GRAY,
    WEAPON_SINGLE, WEAPON_SPREAD, WEAPON_RAPID
)
from game.entities.weapon import Weapon


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Build player sprite
        self.base_size = 36
        self.image = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        self._draw_player_sprite()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 80

        # Stats
        self.speed = 8
        self.max_health = 100
        self.health = self.max_health
        self.gold = 0

        # Weapon
        self.weapon = Weapon(WEAPON_SINGLE)

        # Forward auto-movement speed (slight upward drift)
        self.auto_move_y = 0

    def _draw_player_sprite(self):
        """Draw a simple character sprite."""
        s = self.base_size
        self.image.fill((0, 0, 0, 0))
        # Body
        pygame.draw.rect(self.image, BLUE, (s // 4, s // 4, s // 2, s // 2))
        # Head
        pygame.draw.circle(self.image, (100, 150, 255), (s // 2, s // 4), s // 5)
        # Gun indicator
        pygame.draw.rect(self.image, DARK_GRAY, (s // 2, 0, 4, s // 4))

    @property
    def damage(self):
        return self.weapon.damage

    @property
    def fire_rate(self):
        return self.weapon.fire_rate

    @property
    def bullet_count(self):
        return self.weapon.bullet_count

    @property
    def power(self):
        return self.weapon.get_power_rating()

    def move(self, dx):
        self.rect.x += dx * self.speed
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def update(self, enemies, projectiles_group, all_sprites):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move(-1)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move(1)

        self.auto_fire(enemies, projectiles_group, all_sprites)

    def auto_fire(self, enemies, projectiles_group, all_sprites):
        target = self._find_nearest_enemy(enemies)
        if target:
            self.weapon.fire(
                self.rect.centerx, self.rect.top,
                target, projectiles_group, all_sprites
            )

    def _find_nearest_enemy(self, enemies):
        nearest = None
        min_dist = float('inf')
        for enemy in enemies:
            dx = enemy.rect.centerx - self.rect.centerx
            dy = enemy.rect.centery - self.rect.centery
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist:
                min_dist = dist_sq
                nearest = enemy
        return nearest

    def switch_weapon(self, weapon_type):
        # Preserve bonuses across weapon switches
        old_bonus_dmg = self.weapon.bonus_damage
        old_bonus_rate = self.weapon.bonus_fire_rate
        old_bonus_bullets = self.weapon.bonus_bullets
        self.weapon.set_type(weapon_type)
        self.weapon.bonus_damage = old_bonus_dmg
        self.weapon.bonus_fire_rate = old_bonus_rate
        self.weapon.bonus_bullets = old_bonus_bullets
