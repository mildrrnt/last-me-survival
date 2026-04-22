import random

import pygame

from game.constants import (
    GREEN,
    ORANGE,
    POWERUP_DAMAGE_BOOST,
    POWERUP_RAPID_FIRE,
    POWERUP_SHIELD,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_UPGRADE,
    WEAPON_RAPID,
    WEAPON_SPREAD,
    YELLOW,
    XP_TO_FIRST_LEVEL,
)


UPGRADE_OPTIONS = [
    {"type": "damage", "text": "+10 Damage", "value": 10, "icon_color": RED, "desc": "Hit harder"},
    {"type": "damage", "text": "+20 Damage", "value": 20, "icon_color": RED, "desc": "Hit much harder"},
    {"type": "fire_rate", "text": "Faster Fire", "value": -40, "icon_color": ORANGE, "desc": "Shoot faster"},
    {"type": "multishot", "text": "+1 Bullet", "value": 1, "icon_color": YELLOW, "desc": "Extra projectile"},
    {"type": "multishot", "text": "+2 Bullets", "value": 2, "icon_color": YELLOW, "desc": "Two more shots"},
    {"type": "speed", "text": "+2 Speed", "value": 2, "icon_color": (50, 50, 255), "desc": "Move quicker"},
    {"type": "heal", "text": "Heal 30 HP", "value": 30, "icon_color": GREEN, "desc": "Restore health"},
    {"type": "max_hp", "text": "+25 Max HP", "value": 25, "icon_color": GREEN, "desc": "More durability"},
    {"type": "weapon", "text": "Shotgun", "value": WEAPON_SPREAD, "icon_color": ORANGE, "desc": "Spread weapon"},
    {"type": "weapon", "text": "Machine Gun", "value": WEAPON_RAPID, "icon_color": RED, "desc": "Rapid fire"},
]


class UpgradeSystem:
    def __init__(self, game):
        self.game = game

    def reset_progression(self):
        self.game.xp = 0
        self.game.xp_to_next_level = XP_TO_FIRST_LEVEL
        self.game.upgrade_cards = []

    def trigger_upgrade(self):
        self.game.state = STATE_UPGRADE
        self.game.xp_to_next_level = int(self.game.xp_to_next_level * 1.4)
        self.generate_cards()

    def generate_cards(self):
        self.game.upgrade_cards = []
        chosen = random.sample(UPGRADE_OPTIONS, min(3, len(UPGRADE_OPTIONS)))

        card_width = 120
        card_height = 160
        spacing = 15
        total_width = 3 * card_width + 2 * spacing
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i, data in enumerate(chosen):
            x = start_x + i * (card_width + spacing)
            y = SCREEN_HEIGHT // 2 - card_height // 2
            rect = pygame.Rect(x, y, card_width, card_height)
            self.game.upgrade_cards.append({"data": data, "rect": rect, "hover": False})

    def handle_click(self, pos):
        for card in self.game.upgrade_cards:
            if card["rect"].collidepoint(pos):
                self.apply_upgrade(card["data"])
                return True
        return False

    def apply_upgrade(self, data):
        player = self.game.player
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

        self.game.add_effect_text(player.rect.centerx, player.rect.top - 30, data["text"], positive=True)

    def update_powerup_timers(self):
        dt = 1.0 / 60.0
        expired = []

        for ptype, remaining in self.game.active_powerups.items():
            self.game.active_powerups[ptype] = remaining - dt
            if self.game.active_powerups[ptype] <= 0:
                expired.append(ptype)

        for ptype in expired:
            del self.game.active_powerups[ptype]
            pu_obj = self.game.active_powerup_instances.pop(ptype, None)
            if pu_obj:
                pu_obj.deactivate(self.game.player)

    @staticmethod
    def random_drop_type():
        return random.choice([POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST])
