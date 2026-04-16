import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WEAPON_SINGLE, PLAYER_ANIMATIONS
)
from game.character import Character
from game.weapon import Weapon


class Player(Character):
    def __init__(self):
        super().__init__(hp=100, width=36, height=36)

        # Animation state
        self.current_state = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_duration = 6
        self.dying = False
        self.death_animation_done = False
        self.death_loops = 0
        self.death_loops_total = 3

        # Load sprite sheet animations
        self.animations = {}
        for name, info in PLAYER_ANIMATIONS.items():
            self.animations[name] = self._extract_frames_strip(
                info["file"], info.get("frames")
            )

        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 80

        self.speed = 8
        self.gold = 0
        self.weapon = Weapon(WEAPON_SINGLE)
        self.auto_move_y = 0

        # Mouse drag state
        self.dragging = False

    def set_animation_state(self, state):
        """Switch to a new animation if different from current. No-ops if already in the requested state."""
        if state == self.current_state:
            return
        if state not in self.animations:
            return
        self.current_state = state
        self.frame_index = 0
        self.frame_timer = 0

    def _advance_animation(self):
        """Advance the animation frame timer."""
        self.frame_timer += 1
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0
            self.frame_index += 1

            frames = self.animations[self.current_state]
            if self.frame_index >= len(frames):
                if self.current_state == "die":
                    self.death_loops += 1
                    if self.death_loops >= self.death_loops_total:
                        self.frame_index = len(frames) - 1
                        self.death_animation_done = True
                    else:
                        self.frame_index = 0
                elif self.current_state == "hurt":
                    self.set_animation_state("idle")
                else:
                    self.frame_index = 0

        self.image = self.animations[self.current_state][self.frame_index]

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
        if self.dying:
            self._advance_animation()
            return

        moving = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.move(-1)
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.move(1)
            moving = True

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
                moving = True

        # Set animation based on movement (only if not in hurt state)
        if self.current_state != "hurt":
            if moving:
                self.set_animation_state("move")
            else:
                self.set_animation_state("idle")

        self._advance_animation()
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
