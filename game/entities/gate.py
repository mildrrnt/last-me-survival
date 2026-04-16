import pygame
import random
from game.constants import (
    SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, GREEN, RED, BLACK,
    DARK_GREEN, DARK_RED, YELLOW, ORANGE, BLUE, PURPLE,
    LANE_WIDTH, LANE_COUNT, GOLD_COLOR
)


# Gate effect definitions with display text and values
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

        # Pick an effect
        if effect is None:
            effect = random.choice(GATE_EFFECTS)
        self.effect_type = effect["type"]
        self.value = effect["value"]
        self.positive = effect["positive"]
        self.is_multiplier = effect.get("mult", False)
        self.label_text = effect["text"]

        # Build gate surface
        gate_width = LANE_WIDTH - 8
        gate_height = 40
        self.image = pygame.Surface((gate_width, gate_height), pygame.SRCALPHA)
        self._draw_gate(gate_width, gate_height)
        self.rect = self.image.get_rect()

        # Position in lane
        self.rect.x = lane_index * LANE_WIDTH + 4
        self.rect.y = -60
        self.speed = 3

    def _draw_gate(self, w, h):
        """Draw gate with label."""
        # Background
        bg_color = DARK_GREEN if self.positive else DARK_RED
        border_color = GREEN if self.positive else RED
        pygame.draw.rect(self.image, bg_color, (0, 0, w, h), border_radius=6)
        pygame.draw.rect(self.image, border_color, (0, 0, w, h), 2, border_radius=6)

        # Label text
        font = pygame.font.SysFont(None, 20)
        text_color = WHITE
        text_surf = font.render(self.label_text, True, text_color)
        text_x = (w - text_surf.get_width()) // 2
        text_y = (h - text_surf.get_height()) // 2
        self.image.blit(text_surf, (text_x, text_y))

    # ------------------------------------------------------------------
    # Spec method: affect
    # ------------------------------------------------------------------
    def affect(self, player):
        """Apply this gate's stat change to player."""
        if self.is_multiplier:
            if self.effect_type == 'damage':
                player.weapon.bonus_damage += player.weapon.damage  # Effectively x2
            elif self.effect_type == 'fire_rate':
                player.weapon.bonus_fire_rate -= abs(player.weapon.fire_rate) // 2
        else:
            if self.effect_type == 'damage':
                player.weapon.bonus_damage += self.value
            elif self.effect_type == 'fire_rate':
                player.weapon.bonus_fire_rate += self.value
            elif self.effect_type == 'speed':
                player.speed = max(2, player.speed + self.value)
            elif self.effect_type == 'multishot':
                player.weapon.bonus_bullets += self.value

    # ------------------------------------------------------------------
    # Spec method: move
    # ------------------------------------------------------------------
    def move(self):
        """Scroll this gate downward; remove when it leaves the screen."""
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

    # pygame sprite groups call update() each frame
    def update(self):
        self.move()

    # ------------------------------------------------------------------
    # Spec method: collide
    # ------------------------------------------------------------------
    def collide(self, player, game_manager):
        """Apply effect, trigger visual feedback, and remove this gate."""
        self.affect(player)
        game_manager.particle_manager.spawn_gate_effect(
            player.rect.centerx, player.rect.centery, self.positive
        )
        game_manager.ui_manager.add_effect_text(
            player.rect.centerx, player.rect.top - 20,
            self.label_text, self.positive
        )
        game_manager.screen_shake = max(game_manager.screen_shake, 3)
        self.kill()


class GateRow:
    """Manages a row of gates across lanes with a visual lane-split effect."""

    @staticmethod
    def spawn_gate_row(game_manager, num_gates=3):
        """Spawn a row of gates across random lanes. Ensures mix of positive/negative."""
        # Pick which lanes get gates
        lanes = random.sample(range(LANE_COUNT), min(num_gates, LANE_COUNT))

        # Ensure at least one positive and one negative
        effects = []
        positive_pool = [e for e in GATE_EFFECTS if e["positive"]]
        negative_pool = [e for e in GATE_EFFECTS if not e["positive"]]

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
            game_manager.gates.add(gate)
            game_manager.all_sprites.add(gate)

    @staticmethod
    def draw_lane_dividers(surface, y_start, y_end, offset_x=0, offset_y=0):
        """Draw lane divider lines."""
        for i in range(1, LANE_COUNT):
            x = i * LANE_WIDTH + offset_x
            for y in range(y_start + offset_y, y_end + offset_y, 20):
                pygame.draw.line(surface, (80, 80, 80), (x, y), (x, y + 10), 1)
