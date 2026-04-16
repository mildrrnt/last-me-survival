import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLUE, DARK_GRAY,
    WEAPON_SINGLE
)
from game.character import Character
from game.weapon import Weapon


class Player(Character):
    def __init__(self):
        super().__init__(hp=100, width=36, height=36)
        self._draw_player_sprite()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 80

        self.speed = 8
        self.gold = 0
        self.weapon = Weapon(WEAPON_SINGLE)
        self.auto_move_y = 0

        # Mouse drag state
        self.dragging = False

    def _draw_player_sprite(self):
        s = self.width
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, BLUE, (s // 4, s // 4, s // 2, s // 2))
        pygame.draw.circle(self.image, (100, 150, 255), (s // 2, s // 4), s // 5)
        pygame.draw.rect(self.image, DARK_GRAY, (s // 2, 0, 4, s // 4))

    @property
    def damage(self):
        return self.weapon.damage

    @property
    def power(self):
        return self.weapon.get_power_rating()

    def move(self, dx):
        self.rect.x += dx * self.speed
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def handle_event(self, event):
        """Handle mouse events for drag movement."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

    def update(self, enemies, projectiles_group, all_sprites):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move(-1)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move(1)
<<<<<<< HEAD:game/entities/player.py

        # Mouse drag: follow mouse x position
        if self.dragging:
            mouse_x, _ = pygame.mouse.get_pos()
            dx = mouse_x - self.rect.centerx
            if abs(dx) > 1:
                self.rect.centerx += max(-self.speed, min(self.speed, dx))
                if self.rect.left < 0:
                    self.rect.left = 0
                if self.rect.right > SCREEN_WIDTH:
                    self.rect.right = SCREEN_WIDTH

=======
>>>>>>> 5f559eb (feat: restructured the OOP to be straightforward):game/player.py
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
        old_bonus_dmg = self.weapon.bonus_damage
        old_bonus_rate = self.weapon.bonus_fire_rate
        old_bonus_bullets = self.weapon.bonus_bullets
        self.weapon.set_type(weapon_type)
        self.weapon.bonus_damage = old_bonus_dmg
        self.weapon.bonus_fire_rate = old_bonus_rate
        self.weapon.bonus_bullets = old_bonus_bullets
