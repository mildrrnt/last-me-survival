import pygame

# Screen
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 800
FPS = 60
TITLE = "Last Z Survival"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
DARK_RED = (180, 30, 30)
GREEN = (50, 255, 50)
DARK_GREEN = (30, 180, 30)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
PURPLE = (180, 50, 255)
BROWN = (139, 90, 43)
LIGHT_GREEN = (144, 238, 144)
ZOMBIE_GREEN = (80, 140, 50)
ZOMBIE_DARK = (50, 100, 30)
ZOMBIE_BOSS = (120, 40, 40)
GOLD_COLOR = (255, 215, 0)

# New colors for expanded systems
CYAN = (0, 255, 255)
NEON_GREEN = (57, 255, 20)
BLOOD_RED = (138, 7, 7)
SHIELD_BLUE = (100, 180, 255)
RAPID_YELLOW = (255, 255, 100)
DAMAGE_ORANGE = (255, 120, 30)
GEM_GREEN = (0, 230, 64)
ELITE_GOLD = (255, 200, 50)

# Gameplay Constants
SCROLL_SPEED = 5
LANE_COUNT = 5
LANE_WIDTH = SCREEN_WIDTH // LANE_COUNT

# Run / Wave Config
TOTAL_WAVES = 40
WAVE_ENEMIES_BASE = 3
GATE_INTERVAL_WAVES = 3  # Gates appear every N waves

# Weapon Types
WEAPON_SINGLE = "single"
WEAPON_SPREAD = "spread"
WEAPON_RAPID = "rapid"

# Enemy Types
ENEMY_SMALL = "small"
ENEMY_MEDIUM = "medium"
ENEMY_LARGE = "large"
ENEMY_BOSS = "boss"

# Enemy Config: (width, height, base_hp, base_speed, gold_value)
ENEMY_CONFIG = {
    ENEMY_SMALL:    {"width": 24, "height": 24, "hp": 15,  "speed": 3.0, "gold": 1,  "damage": 12, "color": ZOMBIE_GREEN},
    ENEMY_MEDIUM:   {"width": 32, "height": 32, "hp": 40,  "speed": 2.4, "gold": 3,  "damage": 18, "color": ZOMBIE_DARK},
    ENEMY_LARGE:    {"width": 44, "height": 44, "hp": 90,  "speed": 1.6, "gold": 8,  "damage": 25, "color": DARK_RED},
    ENEMY_BOSS:     {"width": 60, "height": 60, "hp": 300, "speed": 1.0, "gold": 25, "damage": 40, "color": ZOMBIE_BOSS},
}

# Weapon Config: (damage, fire_rate_ms, bullet_count, spread_angle)
WEAPON_CONFIG = {
    WEAPON_SINGLE: {"damage": 8,  "fire_rate": 450, "bullet_count": 1, "spread_angle": 0,  "name": "Pistol",     "color": YELLOW},
    WEAPON_SPREAD: {"damage": 6,  "fire_rate": 550, "bullet_count": 3, "spread_angle": 15, "name": "Shotgun",    "color": ORANGE},
    WEAPON_RAPID:  {"damage": 4,  "fire_rate": 150, "bullet_count": 1, "spread_angle": 3,  "name": "MachineGun", "color": RED},
}

# XP Gem Config
XP_VALUES = {
    ENEMY_SMALL: 1,
    ENEMY_MEDIUM: 3,
    ENEMY_LARGE: 8,
    ENEMY_BOSS: 25,
}
XP_TO_FIRST_LEVEL = 150
GEM_MAGNET_RADIUS = 80
GEM_MAGNET_SPEED = 6
GEM_DRIFT_SPEED = 0.3

# Combo System
COMBO_TIER_1 = 10     # 1.5x XP
COMBO_TIER_2 = 25     # 2.0x XP
COMBO_TIER_3 = 50     # 3.0x XP
COMBO_MULTIPLIERS = {
    0: 1.0,
    COMBO_TIER_1: 1.5,
    COMBO_TIER_2: 2.0,
    COMBO_TIER_3: 3.0,
}

# Power-up Config
POWERUP_DROP_CHANCE = 0.05   # 5% from large/boss/charger
POWERUP_RAPID_FIRE = "rapid_fire"
POWERUP_SHIELD = "shield"
POWERUP_DAMAGE_BOOST = "damage_boost"
POWERUP_DURATIONS = {
    POWERUP_RAPID_FIRE: 5.0,   # seconds
    POWERUP_SHIELD: 3.0,
    POWERUP_DAMAGE_BOOST: 5.0,
}
POWERUP_COLORS = {
    POWERUP_RAPID_FIRE: RAPID_YELLOW,
    POWERUP_SHIELD: SHIELD_BLUE,
    POWERUP_DAMAGE_BOOST: DAMAGE_ORANGE,
}
POWERUP_LABELS = {
    POWERUP_RAPID_FIRE: "RAPID FIRE",
    POWERUP_SHIELD: "SHIELD",
    POWERUP_DAMAGE_BOOST: "DMG BOOST",
}
# Enemies that can drop power-ups
POWERUP_DROP_ENEMIES = {ENEMY_LARGE, ENEMY_BOSS}

# Wave Special Events
WAVE_TYPE_NORMAL = "normal"
WAVE_TYPE_ELITE = "elite"
WAVE_TYPE_SWARM = "swarm"
WAVE_TYPE_MIDBOSS = "midboss"
WAVE_TYPE_BLOOD_MOON = "blood_moon"
WAVE_TYPE_FINAL_BOSS = "final_boss"

# Particle Config
PARTICLE_CAP = 300

# Game States
STATE_START = "START"
STATE_PLAYING = "PLAYING"
STATE_UPGRADE = "UPGRADE"
STATE_GATE_CHOICE = "GATE_CHOICE"
STATE_GAMEOVER = "GAMEOVER"
STATE_WIN = "WIN"
