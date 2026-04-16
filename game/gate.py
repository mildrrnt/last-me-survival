import pygame
import random
from game.constants import (
    SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, GREEN, RED, BLACK,
    DARK_GREEN, DARK_RED,
    LANE_WIDTH, LANE_COUNT
)


GATE_EFFECTS = [
    {"type": "damage",    "positive": True,  "value": 10,  "text": "+10 DMG",      "mult": False},
    {"type": "damage",    "positive": True,  "value": 20,  "text": "+20 DMG",      "mult": False},
    {"type": "damage",    "positive": False, "value": -5,  "text": "-5 DMG",       "mult": False},
    {"type": "fire_rate", "positive": True,  "value": -50, "text": "+Fire Rate",   "mult": False},
    {"type": "fire_rate", "positive": False, "value": 40,  "text": "-Fire Rate",   "mult": False},
    {"type": "multishot", "positive": True,  "value": 1,   "text": "+1 Bullet",    "mult": False},
    {"type": "multishot", "positive": True,  "value": 2,   "text": "+2 Bullets",   "mult": False},
    {"type": "multishot", "positive": False, "value": -1,  "text": "-1 Bullet",    "mult": False},
    {"type": "damage",    "positive": True,  "value": 2,   "text": "x2 DMG",       "mult": True},
    {"type": "fire_rate", "positive": True,  "value": 2,   "text": "x2 Fire Rate", "mult": True},
    {"type": "speed",     "positive": True,  "value": 2,   "text": "+2 Speed",     "mult": False},
    {"type": "speed",     "positive": False, "value": -1,  "text": "-1 Speed",     "mult": False},
]


class Gate(pygame.sprite.Sprite):
    def __init__(self, lane_index, effect=None):
        super().__init__()
        self.lane_index = lane_index

        if effect is None:
            effect = random.choice(GATE_EFFECTS)

        # Spec attributes
        self.value = effect["value"]
        self.type = effect["positive"]       # True = positive gate, False = negative
        self.attr_type = effect["type"]      # which stat to affect (attrType in spec)

        self.is_multiplier = effect.get("mult", False)
        self.label_text = effect["text"]

        gate_width = LANE_WIDTH - 8
        gate_height = 40
        self.image = pygame.Surface((gate_width, gate_height), pygame.SRCALPHA)
        self._draw_gate(gate_width, gate_height)
        self.rect = self.image.get_rect()

        self.rect.x = lane_index * LANE_WIDTH + 4
        self.rect.y = -60
        self.speed = 3

    def _draw_gate(self, w, h):
        bg_color = DARK_GREEN if self.type else DARK_RED
        border_color = GREEN if self.type else RED
        pygame.draw.rect(self.image, bg_color, (0, 0, w, h), border_radius=6)
        pygame.draw.rect(self.image, border_color, (0, 0, w, h), 2, border_radius=6)

        font = pygame.font.SysFont(None, 20)
        text_surf = font.render(self.label_text, True, WHITE)
        text_x = (w - text_surf.get_width()) // 2
        text_y = (h - text_surf.get_height()) // 2
        self.image.blit(text_surf, (text_x, text_y))

    def affect(self, player):
        """Apply this gate's stat change to player."""
        if self.is_multiplier:
            if self.attr_type == 'damage':
                player.weapon.bonus_damage += player.weapon.damage
            elif self.attr_type == 'fire_rate':
                player.weapon.bonus_fire_rate -= abs(player.weapon.fireRate) // 2
        else:
            if self.attr_type == 'damage':
                player.weapon.bonus_damage += self.value
            elif self.attr_type == 'fire_rate':
                player.weapon.bonus_fire_rate += self.value
            elif self.attr_type == 'speed':
                player.speed = max(2, player.speed + self.value)
            elif self.attr_type == 'multishot':
                player.weapon.bonus_bullets += self.value

    def move(self):
        """Scroll this gate downward; remove when it leaves the screen."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    def update(self):
        self.move()

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def collide(self, player, game):
        """Apply effect, trigger visual feedback, and remove this gate."""
        self.affect(player)
        game.spawn_gate_effect(player.rect.centerx, player.rect.centery, self.type)
        game.add_effect_text(player.rect.centerx, player.rect.top - 20, self.label_text, self.type)
        game.screen_shake = max(game.screen_shake, 3)
        self.kill()


def spawn_gate_row(game, num_gates=3):
    """Spawn a row of gates across random lanes with a mix of positive/negative."""
    lanes = random.sample(range(LANE_COUNT), min(num_gates, LANE_COUNT))

    positive_pool = [e for e in GATE_EFFECTS if e["positive"]]
    negative_pool = [e for e in GATE_EFFECTS if not e["positive"]]

    effects = []
    for i in range(len(lanes)):
        if i == 0:
            effects.append(random.choice(positive_pool))
        elif i == 1:
            effects.append(random.choice(negative_pool))
        else:
            effects.append(random.choice(GATE_EFFECTS))

    random.shuffle(effects)

    for i, lane in enumerate(lanes):
        effect = effects[i] if i < len(effects) else random.choice(GATE_EFFECTS)
        gate = Gate(lane, effect)
        game.gates.add(gate)
        game.all_sprites.add(gate)


def draw_lane_dividers(surface, y_start, y_end, offset_x=0, offset_y=0):
    """Draw dashed lane divider lines."""
    for i in range(1, LANE_COUNT):
        x = i * LANE_WIDTH + offset_x
        for y in range(y_start + offset_y, y_end + offset_y, 20):
            pygame.draw.line(surface, (80, 80, 80), (x, y), (x, y + 10), 1)
