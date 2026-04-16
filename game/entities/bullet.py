import pygame
import math
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, YELLOW


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage=10, color=YELLOW):
        super().__init__()
        self.color = color  # Stored for bullet trail particles
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (4, 4), 4)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.speed = 15
        self.damage = damage

        # Normalise direction toward target
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance != 0:
            self.vx = (dx / distance) * self.speed
            self.vy = (dy / distance) * self.speed
        else:
            self.vx = 0
            self.vy = -self.speed

        # Previous position used by ParticleManager for trail spawning
        self.prev_x = float(x)
        self.prev_y = float(y)

    # ------------------------------------------------------------------
    # Spec method: move
    # ------------------------------------------------------------------
    def move(self):
        """Advance this bullet one frame along its trajectory."""
        self.prev_x = float(self.rect.centerx)
        self.prev_y = float(self.rect.centery)

        self.rect.x += self.vx
        self.rect.y += self.vy

        if (self.rect.bottom < -20 or self.rect.top > SCREEN_HEIGHT + 20
                or self.rect.right < -20 or self.rect.left > SCREEN_WIDTH + 20):
            self.kill()

    # pygame sprite groups call update() each frame
    def update(self):
        self.move()

    # ------------------------------------------------------------------
    # Spec method: collide
    # ------------------------------------------------------------------
    def collide(self, enemy, game_manager):
        """Apply this bullet's damage to enemy and remove the bullet."""
        enemy.health -= self.damage
        enemy.hit_flash = 5
        enemy.apply_knockback(self.rect.centerx, self.rect.centery, force=2)
        game_manager.ui_manager.add_damage_text(
            enemy.rect.centerx, enemy.rect.top, self.damage
        )
        self.kill()
