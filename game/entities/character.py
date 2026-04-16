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

    def _extract_frames_grid(self, sheet, row, num_frames, frame_w, frame_h):
        """Slice one row of a sprite sheet into a list of Surfaces."""
        frames = []
        for col in range(num_frames):
            rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
        return frames
    
    def _extract_frames_strip(self, filepath, num_frames):
        """Load a horizontal strip image and slice it into frames."""
        strip = pygame.image.load(filepath).convert_alpha()
        frame_w = strip.get_width() // num_frames
        frame_h = strip.get_height()
        frames = []
        for col in range(num_frames):
            rect = pygame.Rect(col * frame_w, 0, frame_w, frame_h)
            frame = strip.subsurface(rect).copy()
            frames.append(frame)
        return frames