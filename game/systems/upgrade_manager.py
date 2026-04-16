import pygame
import random
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, YELLOW, RED, GREEN,
    ORANGE, BLUE, GRAY, DARK_GRAY, GOLD_COLOR,
    WEAPON_SINGLE, WEAPON_SPREAD, WEAPON_RAPID
)


UPGRADE_OPTIONS = [
    {"type": "damage",    "text": "+10 Damage",      "value": 10,  "icon_color": RED,    "desc": "Hit harder"},
    {"type": "damage",    "text": "+20 Damage",      "value": 20,  "icon_color": RED,    "desc": "Hit much harder"},
    {"type": "fire_rate", "text": "Faster Fire",      "value": -40, "icon_color": ORANGE, "desc": "Shoot faster"},
    {"type": "multishot", "text": "+1 Bullet",        "value": 1,   "icon_color": YELLOW, "desc": "Extra projectile"},
    {"type": "multishot", "text": "+2 Bullets",       "value": 2,   "icon_color": YELLOW, "desc": "Two more shots"},
    {"type": "speed",     "text": "+2 Speed",         "value": 2,   "icon_color": BLUE,   "desc": "Move quicker"},
    {"type": "heal",      "text": "Heal 30 HP",       "value": 30,  "icon_color": GREEN,  "desc": "Restore health"},
    {"type": "max_hp",    "text": "+25 Max HP",       "value": 25,  "icon_color": GREEN,  "desc": "More durability"},
    {"type": "weapon",    "text": "Shotgun",          "value": WEAPON_SPREAD, "icon_color": ORANGE, "desc": "Spread weapon"},
    {"type": "weapon",    "text": "Machine Gun",      "value": WEAPON_RAPID,  "icon_color": RED,    "desc": "Rapid fire"},
]


class UpgradeManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.cards = []
        self.font_title = pygame.font.SysFont(None, 36)
        self.font_card = pygame.font.SysFont(None, 26)
        self.font_desc = pygame.font.SysFont(None, 20)

    def generate_cards(self):
        self.cards = []
        # Pick 3 unique upgrades
        available = list(UPGRADE_OPTIONS)
        chosen = random.sample(available, min(3, len(available)))

        card_width = 120
        card_height = 160
        spacing = 15
        total_w = 3 * card_width + 2 * spacing
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, data in enumerate(chosen):
            x = start_x + i * (card_width + spacing)
            y = SCREEN_HEIGHT // 2 - card_height // 2
            rect = pygame.Rect(x, y, card_width, card_height)
            self.cards.append({"data": data, "rect": rect, "hover": False})

    def draw(self, screen):
        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Title
        title = self.font_title.render("Choose Upgrade", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        # Cards
        mouse_pos = pygame.mouse.get_pos()
        for card in self.cards:
            rect = card["rect"]
            hovered = rect.collidepoint(mouse_pos)
            card["hover"] = hovered

            # Card background
            bg_color = (60, 60, 80) if not hovered else (80, 80, 110)
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)

            # Icon area
            icon_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 50)
            pygame.draw.rect(screen, card["data"]["icon_color"], icon_rect, border_radius=4)

            # Card text
            text = self.font_card.render(card["data"]["text"], True, WHITE)
            screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + 70))

            # Description
            desc = self.font_desc.render(card["data"]["desc"], True, GRAY)
            screen.blit(desc, (rect.x + rect.width // 2 - desc.get_width() // 2, rect.y + 100))

            # Border
            border_color = YELLOW if hovered else WHITE
            border_width = 3 if hovered else 2
            pygame.draw.rect(screen, border_color, rect, border_width, border_radius=8)

    def handle_click(self, pos):
        for card in self.cards:
            if card["rect"].collidepoint(pos):
                self._apply_upgrade(card["data"])
                return True
        return False

    def _apply_upgrade(self, data):
        player = self.game_manager.player
        utype = data["type"]

        if utype == "damage":
            player.weapon.bonus_damage += data["value"]
        elif utype == "fire_rate":
            player.weapon.bonus_fire_rate += data["value"]
        elif utype == "multishot":
            player.weapon.bonus_bullets += data["value"]
        elif utype == "speed":
            player.speed += data["value"]
        elif utype == "heal":
            player.health = min(player.max_health, player.health + data["value"])
        elif utype == "max_hp":
            player.max_health += data["value"]
            player.health += data["value"]
        elif utype == "weapon":
            player.switch_weapon(data["value"])

        self.game_manager.ui_manager.add_effect_text(
            player.rect.centerx, player.rect.top - 30,
            data["text"], positive=True
        )
