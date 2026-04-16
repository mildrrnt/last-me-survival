import pygame
import random
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, RED, GREEN, BLACK, DARK_GRAY,
    STATE_START, STATE_PLAYING, STATE_UPGRADE, STATE_GAMEOVER, STATE_WIN,
    XP_VALUES, XP_TO_FIRST_LEVEL, POWERUP_DROP_CHANCE, POWERUP_DROP_ENEMIES,
    POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST,
    POWERUP_COLORS,
    WAVE_TYPE_BLOOD_MOON
)
from game.entities.player import Player
from game.entities.gate import GateRow
from game.entities.xp_gem import XPGem
from game.entities.powerup import PowerUp
from game.entities.enemy import SplitterEnemy
from game.systems.level_generator import LevelGenerator
from game.systems.particle_manager import ParticleManager
from game.systems.upgrade_manager import UpgradeManager
from game.systems.ui_manager import UIManager
from game.systems.combo_manager import ComboManager


class GameManager:
    def __init__(self, screen):
        self.screen = screen
        self.state = STATE_START

        # Entity groups
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.gates = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        # Player
        self.player = Player()
        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

        # Systems
        self.level_generator = LevelGenerator(self)
        self.upgrade_manager = UpgradeManager(self)
        self.ui_manager = UIManager(self)
        self.particle_manager = ParticleManager()
        self.combo_manager = ComboManager()

        # XP / Level system for upgrades
        self.xp = 0
        self.xp_to_next_level = XP_TO_FIRST_LEVEL

        # Screen shake
        self.screen_shake = 0

        # Background scroll for visual effect
        self.bg_scroll_y = 0

        # Power-up active timers {type: remaining_seconds}
        self.active_powerups = {}

        # Boss kill flash
        self.boss_flash_timer = 0

        # Spawn warning flash
        self.spawn_warning_timer = 0

        # Holds active PowerUp instances so deactivate() can be called when timers expire
        self._active_powerup_instances = {}

    def handle_event(self, event):
        if self.state == STATE_START:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = STATE_PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.state = STATE_PLAYING

        elif self.state == STATE_PLAYING:
            pass  # Input handled in player.update via key polling

        elif self.state == STATE_UPGRADE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.upgrade_manager.handle_click(event.pos):
                    self.state = STATE_PLAYING

        elif self.state in (STATE_GAMEOVER, STATE_WIN):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()

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

        self.level_generator = LevelGenerator(self)
        self.upgrade_manager = UpgradeManager(self)
        self.ui_manager = UIManager(self)
        self.particle_manager = ParticleManager()
        self.combo_manager = ComboManager()
        self.xp = 0
        self.xp_to_next_level = XP_TO_FIRST_LEVEL
        self.screen_shake = 0
        self.bg_scroll_y = 0
        self.active_powerups = {}
        self._active_powerup_instances = {}
        self.boss_flash_timer = 0
        self.spawn_warning_timer = 0

    def update(self):
        if self.state == STATE_PLAYING:
            self.player.update(self.enemies, self.projectiles, self.all_sprites)
            self.level_generator.update()
            self.enemies.update()
            self.projectiles.update()
            self.gates.update()
            self.ui_manager.update()
            self.particle_manager.update()
            self.combo_manager.update()

            # Update gems with player reference for magnet pull
            for gem in self.gems:
                gem.update(self.player.rect)

            # Update powerup sprites
            self.powerups.update()

            # Bullet trail particles
            for proj in self.projectiles:
                self.particle_manager.spawn_bullet_trail(
                    proj.rect.centerx, proj.rect.centery, proj.color
                )

            self.check_collisions()
            self._update_powerup_timers()

            # Screen shake decay
            if self.screen_shake > 0:
                self.screen_shake -= 1

            # Boss flash decay
            if self.boss_flash_timer > 0:
                self.boss_flash_timer -= 1

            # Spawn warning before wave
            if (self.level_generator.spawn_timer >=
                    self.level_generator.spawn_delay - 30):
                self.spawn_warning_timer = 30

            if self.spawn_warning_timer > 0:
                self.spawn_warning_timer -= 1

            # Background scroll
            self.bg_scroll_y = (self.bg_scroll_y + 2) % 40

            # XP check (no more passive XP — only gem pickups)
            if self.xp >= self.xp_to_next_level:
                self.xp = 0
                self.trigger_upgrade()

        elif self.state == STATE_START:
            self.particle_manager.update()

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

    def trigger_upgrade(self):
        self.state = STATE_UPGRADE
        self.xp_to_next_level = int(self.xp_to_next_level * 1.4)
        self.upgrade_manager.generate_cards()

    def trigger_win(self):
        self.state = STATE_WIN

    def check_collisions(self):
        # Bullet -> Enemy  (dokill=False on both sides; Bullet.collide kills the bullet)
        hits = pygame.sprite.groupcollide(self.enemies, self.projectiles, False, False)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if bullet.alive():
                    bullet.collide(enemy, self)

            if enemy.health <= 0:
                    # Gold drop
                    gold = enemy.gold_value
                    self.player.gold += gold
                    self.ui_manager.add_gold_text(enemy.rect.centerx, enemy.rect.top - 15, gold)

                    # Death effects
                    self.particle_manager.spawn_death_explosion(
                        enemy.rect.centerx, enemy.rect.centery, enemy.enemy_type
                    )
                    self.particle_manager.spawn_gold(
                        enemy.rect.centerx, enemy.rect.centery, gold
                    )

                    # Spawn XP gem
                    xp_val = XP_VALUES.get(enemy.enemy_type, 1)
                    gem = XPGem(enemy.rect.centerx, enemy.rect.centery, xp_val)
                    self.gems.add(gem)

                    # Combo
                    self.combo_manager.register_kill()

                    # Boss kill flash
                    if enemy.enemy_type == "boss":
                        self.boss_flash_timer = 10
                        self.screen_shake = max(self.screen_shake, 12)

                    self.screen_shake = max(self.screen_shake, 4)

                    # Splitter: spawn children
                    if isinstance(enemy, SplitterEnemy) and not enemy.has_split:
                        children = enemy.spawn_children()
                        for child in children:
                            self.enemies.add(child)
                            self.all_sprites.add(child)

                    # Power-up drop chance
                    if enemy.enemy_type in POWERUP_DROP_ENEMIES:
                        if random.random() < POWERUP_DROP_CHANCE:
                            ptype = random.choice([
                                POWERUP_RAPID_FIRE, POWERUP_SHIELD, POWERUP_DAMAGE_BOOST
                            ])
                            pu = PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype)
                            self.powerups.add(pu)

                    enemy.kill()

        # Gem -> Player collection (magnet already pulls them close)
        collected_gems = pygame.sprite.spritecollide(self.player, self.gems, True)
        for gem in collected_gems:
            xp_gain = self.combo_manager.get_xp_multiplied(gem.xp_value)
            self.xp += xp_gain
            self.ui_manager.add_damage_text(
                self.player.rect.centerx, self.player.rect.top - 10,
                xp_gain, color=(0, 230, 64)
            )

        # Powerup -> Player collection  (dokill=False; PowerUp.collide kills itself)
        collected_powerups = pygame.sprite.spritecollide(self.player, self.powerups, False)
        for pu in collected_powerups:
            pu.collide(self.player, self)

        # Enemy -> Player
        player_hits = pygame.sprite.spritecollide(self.player, self.enemies, True)
        for enemy in player_hits:
            # Shield blocks damage
            if POWERUP_SHIELD in self.active_powerups:
                self.particle_manager.spawn_explosion(
                    self.player.rect.centerx, self.player.rect.centery,
                    count=15, color=(100, 180, 255)
                )
                continue

            damage_table = {
                "small": 12, "medium": 18, "large": 25, "boss": 40,
                "charger": 22, "splitter": 15
            }
            damage = damage_table.get(enemy.enemy_type, 15)
            self.player.health -= damage

            # Combo reset on damage
            self.combo_manager.on_damage_taken()

            self.ui_manager.add_damage_text(
                self.player.rect.centerx, self.player.rect.top, -damage
            )
            self.screen_shake = max(self.screen_shake, 15)
            self.particle_manager.spawn_explosion(
                self.player.rect.centerx, self.player.rect.centery,
                count=20, color=RED
            )
            if self.player.health <= 0:
                self.player.health = 0
                self.state = STATE_GAMEOVER

        # Player -> Gates  (dokill=False; Gate.collide kills itself)
        gates_hit = pygame.sprite.spritecollide(self.player, self.gates, False)
        for gate in gates_hit:
            gate.collide(self.player, self)

    def draw(self):
        # Shake offset
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)

        if self.state == STATE_START:
            self.ui_manager.draw_start_screen(self.screen)
            return

        # Background
        self._draw_background(offset_x, offset_y)

        # Blood moon tint
        if self.level_generator.blood_moon_active:
            tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tint.fill((138, 7, 7, 35))
            self.screen.blit(tint, (0, 0))

        # Draw lane dividers when gates are nearby
        if len(self.gates) > 0:
            GateRow.draw_lane_dividers(self.screen, 0, SCREEN_HEIGHT, offset_x, offset_y)

        # Draw all sprites with offset
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, (sprite.rect.x + offset_x, sprite.rect.y + offset_y))

        # Draw gems
        for gem in self.gems:
            self.screen.blit(gem.image, (gem.rect.x + offset_x, gem.rect.y + offset_y))

        # Draw powerups
        for pu in self.powerups:
            self.screen.blit(pu.image, (pu.rect.x + offset_x, pu.rect.y + offset_y))

        # Draw enemy health bars
        for enemy in self.enemies:
            enemy.draw_health_bar(self.screen, offset_x, offset_y)

        # Player glow for active power-ups
        if self.active_powerups and self.state == STATE_PLAYING:
            self._draw_player_glow(offset_x, offset_y)

        # Particles
        self.particle_manager.draw(self.screen, offset_x, offset_y)

        # Boss kill screen flash
        if self.boss_flash_timer > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(200 * (self.boss_flash_timer / 10))
            flash.fill((255, 255, 255, alpha))
            self.screen.blit(flash, (0, 0))

        # Spawn warning flash at top
        if self.spawn_warning_timer > 0:
            warn_alpha = int(120 * (self.spawn_warning_timer / 30))
            warn_surf = pygame.Surface((SCREEN_WIDTH, 6), pygame.SRCALPHA)
            warn_surf.fill((255, 50, 50, warn_alpha))
            self.screen.blit(warn_surf, (0, 0))

        # UI (no offset - stays stable)
        self.ui_manager.draw(self.screen)

        # Overlay screens
        if self.state == STATE_GAMEOVER:
            self.ui_manager.draw_game_over(self.screen)
        elif self.state == STATE_WIN:
            self.ui_manager.draw_win_screen(self.screen)
        elif self.state == STATE_UPGRADE:
            self.upgrade_manager.draw(self.screen)

    def _draw_player_glow(self, offset_x, offset_y):
        """Draw a colored glow around player for active power-ups."""
        # Pick the color of the first active power-up
        for ptype in self.active_powerups:
            color = POWERUP_COLORS.get(ptype, (255, 255, 255))
            glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 50), (25, 25), 25)
            x = self.player.rect.centerx - 25 + offset_x
            y = self.player.rect.centery - 25 + offset_y
            self.screen.blit(glow_surf, (x, y))
            break  # Only show one glow

    def _draw_background(self, offset_x, offset_y):
        """Draw a scrolling grid background."""
        self.screen.fill((35, 35, 45))

        # Scrolling grid lines for movement feel
        grid_color = (45, 45, 55)
        grid_spacing = 40

        for y in range(-grid_spacing, SCREEN_HEIGHT + grid_spacing, grid_spacing):
            py = y + (self.bg_scroll_y % grid_spacing) + offset_y
            pygame.draw.line(self.screen, grid_color, (0, py), (SCREEN_WIDTH, py))

        for x in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
            px = x + offset_x
            pygame.draw.line(self.screen, grid_color, (px, 0), (px, SCREEN_HEIGHT))

        # Road/path area (slightly lighter center area)
        road_width = SCREEN_WIDTH - 60
        road_x = 30
        road_color = (40, 40, 52)
        pygame.draw.rect(self.screen, road_color, (road_x + offset_x, 0, road_width, SCREEN_HEIGHT))
