import pygame
import random
import math
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    WHITE, RED, GREEN, BLACK, DARK_GRAY, YELLOW, ORANGE, GRAY, GOLD_COLOR,
    STATE_START, STATE_PLAYING, STATE_UPGRADE, STATE_GAMEOVER, STATE_WIN,
    XP_VALUES, XP_TO_FIRST_LEVEL,
    POWERUP_DROP_CHANCE, POWERUP_DROP_ENEMIES,
    POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST,
    POWERUP_COLORS, POWERUP_LABELS, POWERUP_DURATIONS,
    TOTAL_WAVES, WAVE_ENEMIES_BASE, GATE_INTERVAL_WAVES,
    ENEMY_SMALL, ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS,
    WAVE_TYPE_NORMAL, WAVE_TYPE_ELITE, WAVE_TYPE_SWARM,
    WAVE_TYPE_MIDBOSS, WAVE_TYPE_BLOOD_MOON, WAVE_TYPE_FINAL_BOSS,
    COMBO_TIER_1, COMBO_TIER_2, COMBO_TIER_3, COMBO_MULTIPLIERS,
    PARTICLE_CAP,
    WEAPON_SINGLE, WEAPON_SPREAD, WEAPON_RAPID,
)
from game.player import Player
from game.enemy import Zombie, Boss
from game.gate import Gate, spawn_gate_row, draw_lane_dividers
from game.xp_gem import XPGem
from game.powerup import PowerUp


UPGRADE_OPTIONS = [
    {"type": "damage",    "text": "+10 Damage",  "value": 10,  "icon_color": RED,    "desc": "Hit harder"},
    {"type": "damage",    "text": "+20 Damage",  "value": 20,  "icon_color": RED,    "desc": "Hit much harder"},
    {"type": "fire_rate", "text": "Faster Fire",  "value": -40, "icon_color": ORANGE, "desc": "Shoot faster"},
    {"type": "multishot", "text": "+1 Bullet",    "value": 1,   "icon_color": YELLOW, "desc": "Extra projectile"},
    {"type": "multishot", "text": "+2 Bullets",   "value": 2,   "icon_color": YELLOW, "desc": "Two more shots"},
    {"type": "speed",     "text": "+2 Speed",     "value": 2,   "icon_color": (50, 50, 255), "desc": "Move quicker"},
    {"type": "heal",      "text": "Heal 30 HP",   "value": 30,  "icon_color": GREEN,  "desc": "Restore health"},
    {"type": "max_hp",    "text": "+25 Max HP",   "value": 25,  "icon_color": GREEN,  "desc": "More durability"},
    {"type": "weapon",    "text": "Shotgun",       "value": WEAPON_SPREAD, "icon_color": ORANGE, "desc": "Spread weapon"},
    {"type": "weapon",    "text": "Machine Gun",   "value": WEAPON_RAPID,  "icon_color": RED,    "desc": "Rapid fire"},
]


class Game:
    """
    Object manager for Last Z Survival.
    Owns all game state and delegates to sprite classes for per-object behaviour.
    """

    def __init__(self, screen):
        self.screen = screen
        self.state = STATE_START

        # --- Entity groups ---
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.gates = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        # --- Player ---
        self.player = Player()
        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        # --- Wave / level state ---
        self.spawn_timer = 0
        self.spawn_delay = 180
        self.wave_number = 0
        self.total_waves = TOTAL_WAVES
        self.difficulty_factor = 0.0
        self.enemies_per_wave = WAVE_ENEMIES_BASE
        self.sub_wave_queue = []
        self.sub_wave_timer = 0
        self.sub_wave_delay = 25
        self.gate_timer = 0
        self.gate_delay = 400
        self.waves_since_gate = 0
        self.run_complete = False
        self.current_wave_type = WAVE_TYPE_NORMAL
        self.wave_announcement = ""
        self.announcement_timer = 0
        self.blood_moon_active = False

        # --- Combo state ---
        self.combo_count = 0
        self.highest_combo = 0
        self.combo_multiplier = 1.0
        self.combo_pulse_timer = 0
        self.combo_just_increased = False

        # --- Particles ---
        self.particles = []

        # --- UI ---
        self.font_small = pygame.font.SysFont(None, 20)
        self.font_medium = pygame.font.SysFont(None, 28)
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_xl = pygame.font.SysFont(None, 64)
        self.font_card = pygame.font.SysFont(None, 26)
        self.font_desc = pygame.font.SysFont(None, 20)
        self.floating_texts = []

        # --- Upgrade ---
        self.upgrade_cards = []

        # --- Misc game state ---
        self.xp = 0
        self.xp_to_next_level = XP_TO_FIRST_LEVEL
        self.screen_shake = 0
        self.bg_scroll_y = 0
        self.active_powerups = {}
        self._active_powerup_instances = {}
        self.boss_flash_timer = 0
        self.spawn_warning_timer = 0

    # -------------------------------------------------------------------------
    # Core loop methods (course-standard naming)
    # -------------------------------------------------------------------------

    def process_events(self, event):
        if self.state == STATE_START:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = STATE_PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.state = STATE_PLAYING

        elif self.state == STATE_UPGRADE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self._handle_upgrade_click(event.pos):
                    self.state = STATE_PLAYING

        elif self.state in (STATE_GAMEOVER, STATE_WIN):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()

    def run_logic(self):
        if self.state == STATE_PLAYING:
            self.player.update(self.enemies, self.projectiles, self.all_sprites)
            self._update_level()
            self.enemies.update()
            self.projectiles.update()
            self.gates.update()
            self._update_floating_texts()
            self._update_particles()
            self._update_combo()

            for gem in self.gems:
                gem.update(self.player.rect)

            self.powerups.update()

            for proj in self.projectiles:
                self.spawn_bullet_trail(proj.rect.centerx, proj.rect.centery, proj.color)

            self.check_collisions()
            self._update_powerup_timers()

            if self.screen_shake > 0:
                self.screen_shake -= 1
            if self.boss_flash_timer > 0:
                self.boss_flash_timer -= 1

            if self.spawn_timer >= self.spawn_delay - 30:
                self.spawn_warning_timer = 30
            if self.spawn_warning_timer > 0:
                self.spawn_warning_timer -= 1

            self.bg_scroll_y = (self.bg_scroll_y + 2) % 40

            if self.xp >= self.xp_to_next_level:
                self.xp = 0
                self._trigger_upgrade()

        elif self.state == STATE_START:
            self._update_particles()

    def display_frame(self, screen):
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)

        if self.state == STATE_START:
            self._draw_start_screen(screen)
            return

        self._draw_background(screen, offset_x, offset_y)

        if self.blood_moon_active:
            tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tint.fill((138, 7, 7, 35))
            screen.blit(tint, (0, 0))

        if len(self.gates) > 0:
            draw_lane_dividers(screen, 0, SCREEN_HEIGHT, offset_x, offset_y)

        for sprite in self.all_sprites:
            screen.blit(sprite.image, (sprite.rect.x + offset_x, sprite.rect.y + offset_y))

        for gem in self.gems:
            screen.blit(gem.image, (gem.rect.x + offset_x, gem.rect.y + offset_y))

        for pu in self.powerups:
            screen.blit(pu.image, (pu.rect.x + offset_x, pu.rect.y + offset_y))

        for enemy in self.enemies:
            enemy.draw_health_bar(screen, offset_x, offset_y)

        if self.active_powerups and self.state == STATE_PLAYING:
            self._draw_player_glow(screen, offset_x, offset_y)

        self._draw_particles(screen, offset_x, offset_y)

        if self.boss_flash_timer > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(200 * (self.boss_flash_timer / 10))
            flash.fill((255, 255, 255, alpha))
            screen.blit(flash, (0, 0))

        if self.spawn_warning_timer > 0:
            warn_alpha = int(120 * (self.spawn_warning_timer / 30))
            warn_surf = pygame.Surface((SCREEN_WIDTH, 6), pygame.SRCALPHA)
            warn_surf.fill((255, 50, 50, warn_alpha))
            screen.blit(warn_surf, (0, 0))

        self._draw_ui(screen)

        if self.state == STATE_GAMEOVER:
            self._draw_game_over(screen)
        elif self.state == STATE_WIN:
            self._draw_win_screen(screen)
        elif self.state == STATE_UPGRADE:
            self._draw_upgrade_cards(screen)

    def reset_game(self):
        self.state = STATE_PLAYING
        self.all_sprites.empty()
        self.enemies.empty()
        self.projectiles.empty()
        self.gates.empty()
        self.gems.empty()
        self.powerups.empty()
        self.player_group.empty()

        self.player = Player()
        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        # Reset wave state
        self.spawn_timer = 0
        self.spawn_delay = 180
        self.wave_number = 0
        self.difficulty_factor = 0.0
        self.enemies_per_wave = WAVE_ENEMIES_BASE
        self.sub_wave_queue = []
        self.sub_wave_timer = 0
        self.sub_wave_delay = 25
        self.gate_timer = 0
        self.gate_delay = 400
        self.waves_since_gate = 0
        self.run_complete = False
        self.current_wave_type = WAVE_TYPE_NORMAL
        self.wave_announcement = ""
        self.announcement_timer = 0
        self.blood_moon_active = False

        # Reset combo state
        self.combo_count = 0
        self.highest_combo = 0
        self.combo_multiplier = 1.0
        self.combo_pulse_timer = 0
        self.combo_just_increased = False

        # Reset particles and UI
        self.particles = []
        self.floating_texts = []
        self.upgrade_cards = []

        # Reset misc
        self.xp = 0
        self.xp_to_next_level = XP_TO_FIRST_LEVEL
        self.screen_shake = 0
        self.bg_scroll_y = 0
        self.active_powerups = {}
        self._active_powerup_instances = {}
        self.boss_flash_timer = 0
        self.spawn_warning_timer = 0

    # -------------------------------------------------------------------------
    # Collision handling
    # -------------------------------------------------------------------------

    def check_collisions(self):
        # Bullet -> Enemy
        hits = pygame.sprite.groupcollide(self.enemies, self.projectiles, False, False)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if bullet.alive():
                    bullet.collide(enemy, self)

            if enemy.health <= 0:
                gold = enemy.gold_value
                self.player.gold += gold
                self.add_gold_text(enemy.rect.centerx, enemy.rect.top - 15, gold)
                self.spawn_death_explosion(enemy.rect.centerx, enemy.rect.centery, enemy.enemy_type)
                self.spawn_gold(enemy.rect.centerx, enemy.rect.centery, gold)

                xp_val = XP_VALUES.get(enemy.enemy_type, 1)
                gem = XPGem(enemy.rect.centerx, enemy.rect.centery, xp_val)
                self.gems.add(gem)

                self._register_kill()

                if enemy.enemy_type == ENEMY_BOSS:
                    self.boss_flash_timer = 10
                    self.screen_shake = max(self.screen_shake, 12)

                self.screen_shake = max(self.screen_shake, 4)

                if enemy.enemy_type in POWERUP_DROP_ENEMIES:
                    if random.random() < POWERUP_DROP_CHANCE:
                        ptype = random.choice([POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST])
                        pu = PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype)
                        self.powerups.add(pu)

                enemy.kill()

        # Gem -> Player
        collected_gems = pygame.sprite.spritecollide(self.player, self.gems, True)
        for gem in collected_gems:
            xp_gain = self._get_xp_multiplied(gem.xp_value)
            self.xp += xp_gain
            self.add_damage_text(self.player.rect.centerx, self.player.rect.top - 10,
                                 xp_gain, color=(0, 230, 64))

        # PowerUp -> Player
        collected_powerups = pygame.sprite.spritecollide(self.player, self.powerups, False)
        for pu in collected_powerups:
            pu.collide(self.player, self)

        # Enemy -> Player
        player_hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for enemy in player_hits:
            if POWERUP_SHIELD in self.active_powerups:
                self.spawn_explosion(self.player.rect.centerx, self.player.rect.centery,
                                     count=15, color=(100, 180, 255))
                continue

            damage = enemy.damage
            self.player.health -= damage
            self._on_damage_taken()
            self.add_damage_text(self.player.rect.centerx, self.player.rect.top, -damage)
            self.screen_shake = max(self.screen_shake, 15)
            self.spawn_explosion(self.player.rect.centerx, self.player.rect.centery,
                                 count=20, color=RED)
            if self.player.health <= 0:
                self.player.health = 0
                self.state = STATE_GAMEOVER

        # Player -> Gates
        gates_hit = pygame.sprite.spritecollide(self.player, self.gates, False)
        for gate in gates_hit:
            gate.collide(self.player, self)

    # -------------------------------------------------------------------------
    # Wave / level methods
    # -------------------------------------------------------------------------

    def _update_level(self):
        if self.run_complete:
            self._process_sub_wave()
            if len(self.sub_wave_queue) == 0 and len(self.enemies) == 0:
                self.trigger_win()
            return

        self._process_sub_wave()

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self._spawn_wave()

        self.gate_timer += 1
        if self.gate_timer >= self.gate_delay:
            self.gate_timer = 0
            spawn_gate_row(self, random.randint(2, 4))

        if self.announcement_timer > 0:
            self.announcement_timer -= 1

    def _process_sub_wave(self):
        if not self.sub_wave_queue:
            return
        self.sub_wave_timer += 1
        if self.sub_wave_timer >= self.sub_wave_delay:
            self.sub_wave_timer = 0
            burst = min(2, len(self.sub_wave_queue))
            for _ in range(burst):
                enemy_type = self.sub_wave_queue.pop(0)
                enemy = self._create_enemy(enemy_type)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)

    def _create_enemy(self, enemy_type):
        speed_bonus = self.difficulty_factor * 0.2
        hp_bonus = self.difficulty_factor * 5
        if self.blood_moon_active:
            speed_bonus += 1.0

        if enemy_type == ENEMY_BOSS:
            enemy = Boss(speed_bonus=speed_bonus, hp_bonus=hp_bonus)
        else:
            enemy = Zombie(enemy_type=enemy_type, speed_bonus=speed_bonus, hp_bonus=hp_bonus)

        if self.current_wave_type == WAVE_TYPE_ELITE:
            enemy.set_elite()

        return enemy

    def _spawn_wave(self):
        self.wave_number += 1
        self.waves_since_gate += 1
        self.current_wave_type = self._classify_wave(self.wave_number)
        self._set_wave_announcement()

        if self.current_wave_type == WAVE_TYPE_FINAL_BOSS:
            self.run_complete = True
            self._spawn_final_boss_wave()
            return
        elif self.current_wave_type == WAVE_TYPE_MIDBOSS:
            self._spawn_midboss_wave()
        elif self.current_wave_type == WAVE_TYPE_BLOOD_MOON:
            self.blood_moon_active = True
            self._spawn_blood_moon_wave()
        elif self.current_wave_type == WAVE_TYPE_SWARM:
            self._spawn_swarm_wave()
        elif self.current_wave_type == WAVE_TYPE_ELITE:
            self._spawn_elite_wave()
        else:
            self.sub_wave_queue.extend(self._get_wave_composition())

        if self.wave_number <= 20:
            self.difficulty_factor += 0.10
        else:
            self.difficulty_factor += 0.25
        self.enemies_per_wave = WAVE_ENEMIES_BASE + self.wave_number // 3

        if self.spawn_delay > 80:
            self.spawn_delay -= 3
        if self.sub_wave_delay > 12:
            self.sub_wave_delay -= 0.5

        if self.waves_since_gate >= GATE_INTERVAL_WAVES:
            self.waves_since_gate = 0
            spawn_gate_row(self, random.randint(2, 4))

    def _classify_wave(self, wave_num):
        if wave_num == 40:
            return WAVE_TYPE_FINAL_BOSS
        if wave_num == 30:
            return WAVE_TYPE_BLOOD_MOON
        if wave_num == 20:
            return WAVE_TYPE_MIDBOSS
        if wave_num % 10 == 0:
            return WAVE_TYPE_SWARM
        if wave_num % 5 == 0:
            return WAVE_TYPE_ELITE
        return WAVE_TYPE_NORMAL

    def _set_wave_announcement(self):
        announcements = {
            WAVE_TYPE_ELITE: "ELITE WAVE",
            WAVE_TYPE_SWARM: "SWARM!",
            WAVE_TYPE_MIDBOSS: "MID-BOSS!",
            WAVE_TYPE_BLOOD_MOON: "BLOOD MOON",
            WAVE_TYPE_FINAL_BOSS: "FINAL BOSS",
        }
        text = announcements.get(self.current_wave_type, "")
        if text:
            self.wave_announcement = text
            self.announcement_timer = 180
        else:
            self.wave_announcement = f"Wave {self.wave_number}"
            self.announcement_timer = 60

    def _get_wave_composition(self):
        enemies = []
        count = min(self.enemies_per_wave + int(self.difficulty_factor), 15)
        for _ in range(count):
            roll = random.random()
            if self.wave_number <= 3:
                enemies.append(ENEMY_SMALL)
            elif self.wave_number <= 6:
                enemies.append(ENEMY_SMALL if roll < 0.5 else ENEMY_MEDIUM)
            elif self.wave_number <= 12:
                if roll < 0.20:
                    enemies.append(ENEMY_SMALL)
                elif roll < 0.55:
                    enemies.append(ENEMY_MEDIUM)
                else:
                    enemies.append(ENEMY_LARGE)
            elif self.wave_number <= 25:
                if roll < 0.10:
                    enemies.append(ENEMY_SMALL)
                elif roll < 0.30:
                    enemies.append(ENEMY_MEDIUM)
                elif roll < 0.65:
                    enemies.append(ENEMY_LARGE)
                else:
                    enemies.append(ENEMY_BOSS)
            else:
                if roll < 0.15:
                    enemies.append(ENEMY_MEDIUM)
                elif roll < 0.45:
                    enemies.append(ENEMY_LARGE)
                else:
                    enemies.append(ENEMY_BOSS)
        return enemies

    def _spawn_elite_wave(self):
        count = max(3, self.enemies_per_wave // 2)
        for _ in range(count):
            self.sub_wave_queue.append(random.choice([ENEMY_MEDIUM, ENEMY_LARGE]))

    def _spawn_swarm_wave(self):
        count = min(25, self.enemies_per_wave * 3)
        for _ in range(count):
            self.sub_wave_queue.append(ENEMY_SMALL)

    def _spawn_midboss_wave(self):
        self.sub_wave_queue.append(ENEMY_BOSS)
        for _ in range(6):
            self.sub_wave_queue.append(ENEMY_MEDIUM if random.random() < 0.5 else ENEMY_LARGE)

    def _spawn_blood_moon_wave(self):
        count = min(18, self.enemies_per_wave * 2)
        for _ in range(count):
            self.sub_wave_queue.append(random.choice([ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS]))

    def _spawn_final_boss_wave(self):
        for _ in range(2):
            boss = Boss(speed_bonus=0.6, hp_bonus=self.difficulty_factor * 12)
            self.enemies.add(boss)
            self.all_sprites.add(boss)
        for _ in range(5):
            e = Zombie(enemy_type=ENEMY_LARGE,
                       speed_bonus=self.difficulty_factor * 0.15,
                       hp_bonus=self.difficulty_factor * 4)
            self.enemies.add(e)
            self.all_sprites.add(e)
        for _ in range(6):
            e = Zombie(enemy_type=ENEMY_MEDIUM,
                       speed_bonus=self.difficulty_factor * 0.2,
                       hp_bonus=self.difficulty_factor * 4)
            self.enemies.add(e)
            self.all_sprites.add(e)

    def trigger_win(self):
        self.state = STATE_WIN

    # -------------------------------------------------------------------------
    # Upgrade methods
    # -------------------------------------------------------------------------

    def _trigger_upgrade(self):
        self.state = STATE_UPGRADE
        self.xp_to_next_level = int(self.xp_to_next_level * 1.4)
        self._generate_upgrade_cards()

    def _generate_upgrade_cards(self):
        self.upgrade_cards = []
        chosen = random.sample(UPGRADE_OPTIONS, min(3, len(UPGRADE_OPTIONS)))

        card_width = 120
        card_height = 160
        spacing = 15
        total_w = 3 * card_width + 2 * spacing
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, data in enumerate(chosen):
            x = start_x + i * (card_width + spacing)
            y = SCREEN_HEIGHT // 2 - card_height // 2
            rect = pygame.Rect(x, y, card_width, card_height)
            self.upgrade_cards.append({"data": data, "rect": rect, "hover": False})

    def _handle_upgrade_click(self, pos):
        for card in self.upgrade_cards:
            if card["rect"].collidepoint(pos):
                self._apply_upgrade(card["data"])
                return True
        return False

    def _apply_upgrade(self, data):
        player = self.player
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

        self.add_effect_text(player.rect.centerx, player.rect.top - 30, data["text"], positive=True)

    # -------------------------------------------------------------------------
    # Combo methods
    # -------------------------------------------------------------------------

    def _register_kill(self):
        self.combo_count += 1
        self.combo_just_increased = True
        self.combo_pulse_timer = 15
        if self.combo_count > self.highest_combo:
            self.highest_combo = self.combo_count
        self._update_combo_multiplier()

    def _on_damage_taken(self):
        self.combo_count = 0
        self.combo_multiplier = 1.0

    def _update_combo_multiplier(self):
        if self.combo_count >= COMBO_TIER_3:
            self.combo_multiplier = COMBO_MULTIPLIERS[COMBO_TIER_3]
        elif self.combo_count >= COMBO_TIER_2:
            self.combo_multiplier = COMBO_MULTIPLIERS[COMBO_TIER_2]
        elif self.combo_count >= COMBO_TIER_1:
            self.combo_multiplier = COMBO_MULTIPLIERS[COMBO_TIER_1]
        else:
            self.combo_multiplier = 1.0

    def _get_xp_multiplied(self, base_xp):
        return int(base_xp * self.combo_multiplier)

    def _update_combo(self):
        if self.combo_pulse_timer > 0:
            self.combo_pulse_timer -= 1
        else:
            self.combo_just_increased = False

    # -------------------------------------------------------------------------
    # Particle methods
    # -------------------------------------------------------------------------

    def spawn_explosion(self, x, y, count=10, color=RED):
        count = min(count, PARTICLE_CAP - len(self.particles))
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-5, 5),
                'vy': random.uniform(-5, 5),
                'life': random.randint(20, 40),
                'color': color,
                'size': random.randint(2, 6),
                'gravity': 0.1
            })

    def spawn_death_explosion(self, x, y, enemy_type="small"):
        base_count = {"small": 8, "medium": 14, "large": 22, "boss": 40}.get(enemy_type, 10)
        count = min(base_count, PARTICLE_CAP - len(self.particles))
        colors = [RED, ORANGE, YELLOW, WHITE]
        for _ in range(count):
            speed = random.uniform(2, 10)
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-speed, speed),
                'vy': random.uniform(-speed, speed),
                'life': random.randint(15, 55),
                'color': random.choice(colors),
                'size': random.randint(3, 8),
                'gravity': 0.05
            })

    def spawn_gold(self, x, y, amount=1):
        count = min(amount * 2, 10, PARTICLE_CAP - len(self.particles))
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-4, -1),
                'life': random.randint(20, 40),
                'color': GOLD_COLOR,
                'size': random.randint(2, 4),
                'gravity': 0.1
            })

    def spawn_gate_effect(self, x, y, positive=True):
        count = min(20, PARTICLE_CAP - len(self.particles))
        color = GREEN if positive else RED
        for _ in range(count):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(2, 5)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.randint(20, 50),
                'color': color,
                'size': random.randint(3, 6),
                'gravity': 0.0
            })

    def spawn_bullet_trail(self, x, y, color=YELLOW):
        if len(self.particles) >= PARTICLE_CAP:
            return
        trail_color = (max(0, color[0] // 2), max(0, color[1] // 2), max(0, color[2] // 2))
        self.particles.append({
            'x': x + random.uniform(-1, 1),
            'y': y + random.uniform(-1, 1),
            'vx': random.uniform(-0.3, 0.3),
            'vy': random.uniform(-0.3, 0.3),
            'life': random.randint(5, 12),
            'color': trail_color,
            'size': random.uniform(1.5, 3),
            'gravity': 0.0
        })

    def _update_particles(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += p.get('gravity', 0)
            p['life'] -= 1
            p['size'] = max(0, p['size'] - 0.05)
        self.particles = [p for p in self.particles if p['life'] > 0]

    def _draw_particles(self, screen, offset_x=0, offset_y=0):
        for p in self.particles:
            size = max(1, int(p['size']))
            pygame.draw.circle(screen, p['color'],
                               (int(p['x'] + offset_x), int(p['y'] + offset_y)), size)

    # -------------------------------------------------------------------------
    # Powerup timer
    # -------------------------------------------------------------------------

    def _update_powerup_timers(self):
        dt = 1.0 / 60.0
        expired = []
        for ptype, remaining in self.active_powerups.items():
            self.active_powerups[ptype] = remaining - dt
            if self.active_powerups[ptype] <= 0:
                expired.append(ptype)
        for ptype in expired:
            del self.active_powerups[ptype]
            pu_obj = self._active_powerup_instances.pop(ptype, None)
            if pu_obj:
                pu_obj.deactivate(self.player)

    # -------------------------------------------------------------------------
    # UI / floating text methods
    # -------------------------------------------------------------------------

    def add_damage_text(self, x, y, value, color=None):
        if color is None:
            color = RED if value < 0 else WHITE
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': str(abs(value)) if value >= 0 else str(value),
            'timer': 45, 'color': color, 'scale': 1.0
        })

    def add_gold_text(self, x, y, amount):
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': f"+{amount}",
            'timer': 40, 'color': GOLD_COLOR, 'scale': 0.8
        })

    def add_effect_text(self, x, y, text, positive=True):
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': text,
            'timer': 60, 'color': GREEN if positive else RED, 'scale': 1.2
        })

    def _update_floating_texts(self):
        for ft in self.floating_texts:
            ft['y'] -= 1.2
            ft['timer'] -= 1
        self.floating_texts = [ft for ft in self.floating_texts if ft['timer'] > 0]

    # -------------------------------------------------------------------------
    # Drawing methods
    # -------------------------------------------------------------------------

    def _draw_ui(self, screen):
        self._draw_floating_texts(screen)
        self._draw_health_bar(screen)
        self._draw_gold(screen)
        self._draw_power_indicator(screen)
        self._draw_wave_progress(screen)
        self._draw_weapon_name(screen)
        self._draw_combo_counter(screen)
        self._draw_powerup_timers(screen)
        self._draw_wave_announcement(screen)
        self._draw_xp_bar(screen)

    def _draw_floating_texts(self, screen):
        for ft in self.floating_texts:
            alpha = min(255, ft['timer'] * 8)
            text_surf = self.font_medium.render(ft['text'], True, ft['color'])
            if ft['timer'] < 15:
                text_surf.set_alpha(alpha)
            screen.blit(text_surf, (ft['x'] - text_surf.get_width() // 2, ft['y']))

    def _draw_health_bar(self, screen):
        bar_w, bar_h = 160, 16
        x, y = 10, 10
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        fill = max(0, int(bar_w * (self.player.health / self.player.max_health)))
        fill_color = GREEN if self.player.health > 50 else ORANGE if self.player.health > 25 else RED
        pygame.draw.rect(screen, fill_color, (x, y, fill, bar_h), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 2, border_radius=3)
        hp_text = self.font_small.render(f"{self.player.health}/{self.player.max_health}", True, WHITE)
        screen.blit(hp_text, (x + bar_w // 2 - hp_text.get_width() // 2, y + 1))

    def _draw_gold(self, screen):
        gold_text = self.font_medium.render(f"{self.player.gold}", True, GOLD_COLOR)
        icon_x = SCREEN_WIDTH - 10 - gold_text.get_width() - 22
        icon_y = 12
        pygame.draw.circle(screen, GOLD_COLOR, (icon_x + 8, icon_y + 8), 8)
        pygame.draw.circle(screen, (200, 170, 0), (icon_x + 8, icon_y + 8), 8, 2)
        g_surf = self.font_small.render("G", True, BLACK)
        screen.blit(g_surf, (icon_x + 3, icon_y + 2))
        screen.blit(gold_text, (icon_x + 20, icon_y))

    def _draw_power_indicator(self, screen):
        x, y = 10, 32
        label = self.font_small.render("PWR", True, GRAY)
        screen.blit(label, (x, y))
        value = self.font_medium.render(str(self.player.power), True, YELLOW)
        screen.blit(value, (x + 35, y - 2))

    def _draw_wave_progress(self, screen):
        progress = min(1.0, self.wave_number / self.total_waves)
        bar_w, bar_h = 140, 10
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 6
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, (100, 200, 255), (x, y, int(bar_w * progress), bar_h), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 1, border_radius=3)
        wave_text = self.font_small.render(
            f"Wave {min(self.wave_number, self.total_waves)}/{self.total_waves}", True, WHITE)
        screen.blit(wave_text, (x + bar_w // 2 - wave_text.get_width() // 2, y + 12))

    def _draw_weapon_name(self, screen):
        self.player.weapon.draw(screen, 10, 52)

    def _draw_combo_counter(self, screen):
        if self.combo_count < COMBO_TIER_1:
            return
        x, y = SCREEN_WIDTH - 10, 36
        shake_x = shake_y = 0
        if self.combo_just_increased:
            shake_x = int(math.sin(self.combo_pulse_timer * 2) * 3)
            shake_y = int(math.cos(self.combo_pulse_timer * 3) * 2)
        color = RED if self.combo_multiplier >= 3.0 else ORANGE if self.combo_multiplier >= 2.0 else YELLOW
        combo_text = self.font_medium.render(f"x{self.combo_count}", True, color)
        screen.blit(combo_text, (x - combo_text.get_width() + shake_x, y + shake_y))
        mult_text = self.font_small.render(f"{self.combo_multiplier}x XP", True, color)
        screen.blit(mult_text, (x - mult_text.get_width() + shake_x, y + 22 + shake_y))

    def _draw_powerup_timers(self, screen):
        if not self.active_powerups:
            return
        y_offset = 70
        bar_w, bar_h = 80, 10
        for ptype, remaining in self.active_powerups.items():
            color = POWERUP_COLORS.get(ptype, WHITE)
            label = POWERUP_LABELS.get(ptype, "???")
            max_dur = POWERUP_DURATIONS.get(ptype, 5.0)
            lbl = self.font_small.render(label, True, color)
            screen.blit(lbl, (10, y_offset))
            bar_y = y_offset + 14
            pygame.draw.rect(screen, DARK_GRAY, (10, bar_y, bar_w, bar_h), border_radius=2)
            fill = max(0, int(bar_w * (remaining / max_dur)))
            pygame.draw.rect(screen, color, (10, bar_y, fill, bar_h), border_radius=2)
            pygame.draw.rect(screen, WHITE, (10, bar_y, bar_w, bar_h), 1, border_radius=2)
            y_offset += 28

    def _draw_wave_announcement(self, screen):
        if self.announcement_timer <= 0 or not self.wave_announcement:
            return
        color_map = {
            WAVE_TYPE_ELITE: GOLD_COLOR,
            WAVE_TYPE_SWARM: WHITE,
            WAVE_TYPE_MIDBOSS: RED,
            WAVE_TYPE_BLOOD_MOON: (200, 30, 30),
            WAVE_TYPE_FINAL_BOSS: RED,
        }
        color = color_map.get(self.current_wave_type, (180, 180, 180))
        if self.announcement_timer > 150:
            alpha = int(255 * ((180 - self.announcement_timer) / 30))
        elif self.announcement_timer < 30:
            alpha = int(255 * (self.announcement_timer / 30))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        font = self.font_xl if self.current_wave_type in color_map else self.font_large
        text_surf = font.render(self.wave_announcement, True, color)
        text_surf.set_alpha(alpha)
        screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, SCREEN_HEIGHT // 3))

    def _draw_xp_bar(self, screen):
        if self.xp_to_next_level <= 0:
            return
        bar_w, bar_h = 100, 6
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 28
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=2)
        fill = int(bar_w * min(1.0, self.xp / self.xp_to_next_level))
        pygame.draw.rect(screen, (0, 230, 64), (x, y, fill, bar_h), border_radius=2)
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_w, bar_h), 1, border_radius=2)

    def _draw_upgrade_cards(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("Choose Upgrade", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        mouse_pos = pygame.mouse.get_pos()
        for card in self.upgrade_cards:
            rect = card["rect"]
            hovered = rect.collidepoint(mouse_pos)
            card["hover"] = hovered

            bg_color = (80, 80, 110) if hovered else (60, 60, 80)
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)

            icon_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 50)
            pygame.draw.rect(screen, card["data"]["icon_color"], icon_rect, border_radius=4)

            text = self.font_card.render(card["data"]["text"], True, WHITE)
            screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + 70))

            desc = self.font_desc.render(card["data"]["desc"], True, GRAY)
            screen.blit(desc, (rect.x + rect.width // 2 - desc.get_width() // 2, rect.y + 100))

            border_color = YELLOW if hovered else WHITE
            pygame.draw.rect(screen, border_color, rect, 3 if hovered else 2, border_radius=8)

    def _draw_start_screen(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 20, 30))
        screen.blit(overlay, (0, 0))
        title = self.font_xl.render("LAST Z SURVIVAL", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        sub = self.font_medium.render("Survive the zombie horde!", True, GRAY)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 280))
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            instr = self.font_medium.render("Press SPACE to Start", True, WHITE)
            screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 450))
        for i, line in enumerate(["A/D or Arrow Keys to Move",
                                   "Auto-fire at nearest zombie",
                                   "Choose gates wisely!"]):
            surf = self.font_small.render(line, True, GRAY)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 530 + i * 25))

    def _draw_game_over(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        title = self.font_xl.render("GAME OVER", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        stats = self.font_medium.render(
            f"Wave {self.wave_number}  |  Gold: {self.player.gold}", True, GOLD_COLOR)
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))
        if self.highest_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {self.highest_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        restart = self.font_medium.render("Press R to Restart", True, WHITE)
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    def _draw_win_screen(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 20, 0))
        screen.blit(overlay, (0, 0))
        title = self.font_xl.render("SURVIVED!", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
        stats = self.font_medium.render(
            f"Gold: {self.player.gold}  |  Power: {self.player.power}", True, GOLD_COLOR)
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))
        sub = self.font_medium.render("You cleared all 40 waves!", True, WHITE)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
        if self.highest_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {self.highest_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
        restart = self.font_medium.render("Press R to Play Again", True, WHITE)
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 90))

    def _draw_background(self, screen, offset_x, offset_y):
        screen.fill((35, 35, 45))
        grid_color = (45, 45, 55)
        grid_spacing = 40
        for y in range(-grid_spacing, SCREEN_HEIGHT + grid_spacing, grid_spacing):
            py = y + (self.bg_scroll_y % grid_spacing) + offset_y
            pygame.draw.line(screen, grid_color, (0, py), (SCREEN_WIDTH, py))
        for x in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
            px = x + offset_x
            pygame.draw.line(screen, grid_color, (px, 0), (px, SCREEN_HEIGHT))
        road_color = (40, 40, 52)
        pygame.draw.rect(screen, road_color, (30 + offset_x, 0, SCREEN_WIDTH - 60, SCREEN_HEIGHT))

    def _draw_player_glow(self, screen, offset_x, offset_y):
        for ptype in self.active_powerups:
            color = POWERUP_COLORS.get(ptype, (255, 255, 255))
            glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 50), (25, 25), 25)
            x = self.player.rect.centerx - 25 + offset_x
            y = self.player.rect.centery - 25 + offset_y
            screen.blit(glow_surf, (x, y))
            break
