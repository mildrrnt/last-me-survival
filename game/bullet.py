import pygame
import math
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, YELLOW


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, damage=10, color=YELLOW):
        super().__init__()
        self.color = color
        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (4, 4), 4)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.speed = 15
        self.damage = damage

        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance != 0:
            self.speed_x = (dx / distance) * self.speed
            self.speed_y = (dy / distance) * self.speed
        else:
            self.speed_x = 0
            self.speed_y = -self.speed

        self.prev_x = float(x)
        self.prev_y = float(y)

    def move(self):
        """Advance this bullet one frame along its trajectory."""
        self.prev_x = float(self.rect.centerx)
        self.prev_y = float(self.rect.centery)

        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if (self.rect.bottom < -20 or self.rect.top > SCREEN_HEIGHT + 20
                or self.rect.right < -20 or self.rect.left > SCREEN_WIDTH + 20):
            self.kill()

    def update(self):
        self.move()

    def collide(self, enemy, game):
        """Apply this bullet's damage to enemy and remove the bullet."""
        enemy.health -= self.damage
        enemy.hit_flash = 5
        enemy.apply_knockback(self.rect.centerx, self.rect.centery, force=2)
        game.add_damage_text(enemy.rect.centerx, enemy.rect.top, self.damage)
        self.kill()
