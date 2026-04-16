import pygame
from game.constants import SCREEN_WIDTH


class Character(pygame.sprite.Sprite):
    """Base class for all game characters (player, zombies, bosses)."""

    def __init__(self, hp, width, height):
        super().__init__()
        self.max_health = hp
        self.health = hp
        self.width = width
        self.height = height
        self.speed = 0

        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

    def walk(self, dx, dy=0):
        """Move the character by (dx, dy), clamped to screen bounds."""
        self.rect.x += int(dx * self.speed)
        self.rect.y += int(dy * self.speed)

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def draw(self, surface):
        """Draw the character onto a surface."""
        surface.blit(self.image, self.rect)

    def collide(self, other):
        """Check collision with another sprite."""
        return pygame.sprite.collide_rect(self, other)
