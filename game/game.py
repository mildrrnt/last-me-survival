import random

import pygame

from game.constants import (
    COMBO_MULTIPLIERS,
    COMBO_TIER_1,
    COMBO_TIER_2,
    COMBO_TIER_3,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_GAMEOVER,
    STATE_PAUSE,
    STATE_PLAYING,
    STATE_START,
    STATE_UPGRADE,
    STATE_WIN,
)
from game.entities.player import Player
from game.systems.collision_system import CollisionSystem
from game.systems.particle_system import ParticleSystem
from game.systems.render_system import RenderSystem
from game.systems.upgrade_system import UpgradeSystem
from game.systems.wave_system import WaveSystem


class Game:
    """Facade coordinator for game state, systems, and frame loop."""

    def __init__(self, screen):
        self.screen = screen
        self.state = STATE_START

        self._create_groups()
        self._create_player()
        self._create_ui_buttons()

        self.combo_count = 0
        self.highest_combo = 0
        self.combo_multiplier = 1.0
        self.combo_pulse_timer = 0
        self.combo_just_increased = False

        self.particles = []
        self.upgrade_cards = []
        self.active_powerups = {}
        self._active_powerup_instances = {}

        self.screen_shake = 0
        self.bg_scroll_y = 0
        self.boss_flash_timer = 0
        self.spawn_warning_timer = 0

        # Initialized by subsystem reset methods; declared here for clarity and tooling.
        self.xp = 0
        self.xp_to_next_level = 0
        self.spawn_timer = 0
        self.spawn_delay = 0

        self.wave_system = WaveSystem(self)
        self.upgrade_system = UpgradeSystem(self)
        self.particle_system = ParticleSystem(self)
        self.render_system = RenderSystem(self)
        self.collision_system = CollisionSystem(self)

        self.auto_aim = True

        self.wave_system.reset()
        self.upgrade_system.reset_progression()

    def _create_groups(self):
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.gates = pygame.sprite.Group()
        self.gems = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

    def _create_player(self):
        self.player = Player()
        self.player_group.add(self.player)
        self.all_sprites.add(self.player)

    def _create_ui_buttons(self):
        btn_w, btn_h = 180, 44
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        self.pause_resume_rect = pygame.Rect(cx - btn_w // 2, cy + 40, btn_w, btn_h)
        self.pause_resign_rect = pygame.Rect(cx - btn_w // 2, cy + 100, btn_w, btn_h)
        self.end_restart_rect = pygame.Rect(cx - btn_w // 2, cy + 80, btn_w, btn_h)
        self.end_home_rect = pygame.Rect(cx - btn_w // 2, cy + 140, btn_w, btn_h)
        self.toggle_aim_rect = pygame.Rect(cx - btn_w // 2, cy + 200, btn_w, btn_h)

    def process_events(self, event):
        if self.state == STATE_START:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.state = STATE_PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.toggle_aim_rect.collidepoint(event.pos):
                    self.auto_aim = not self.auto_aim
                else:
                    self.state = STATE_PLAYING

        elif self.state == STATE_PLAYING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = STATE_PAUSE
            self.player.handle_event(event)

        elif self.state == STATE_PAUSE:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.state = STATE_PLAYING
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.pause_resume_rect.collidepoint(event.pos):
                    self.state = STATE_PLAYING
                elif self.pause_resign_rect.collidepoint(event.pos):
                    self.state = STATE_GAMEOVER
                elif self.toggle_aim_rect.collidepoint(event.pos):
                    self.auto_aim = not self.auto_aim

        elif self.state == STATE_UPGRADE:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.upgrade_system.handle_click(event.pos):
                    self.state = STATE_PLAYING

        elif self.state in (STATE_GAMEOVER, STATE_WIN):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.end_restart_rect.collidepoint(event.pos):
                    self.reset_game()
                elif self.end_home_rect.collidepoint(event.pos):
                    self.reset_game()
                    self.state = STATE_START

    def run_logic(self):
        if self.state == STATE_PLAYING:
            self.player.update(self.enemies, self.projectiles, self.all_sprites, self.auto_aim)

            if self.player.dying and self.player.death_animation_done:
                self.state = STATE_GAMEOVER
                return

            self.wave_system.update()
            self.enemies.update()
            self.projectiles.update()
            self.gates.update()
            self.render_system.update_floating_texts()
            self.particle_system.update()
            self._update_combo()

            player_rect = self.player.rect
            for gem in self.gems:
                gem.update(player_rect)

            self.powerups.update()

            for proj in self.projectiles:
                self.particle_system.spawn_bullet_trail(proj.rect.centerx, proj.rect.centery, proj.color)

            self.collision_system.check_collisions()
            self.upgrade_system.update_powerup_timers()
            self._update_transient_effects()

            if self.xp >= self.xp_to_next_level:
                self.xp = 0
                self.upgrade_system.trigger_upgrade()

        elif self.state == STATE_START:
            self.particle_system.update()

    def _update_transient_effects(self):
        if self.screen_shake > 0:
            self.screen_shake -= 1
        if self.boss_flash_timer > 0:
            self.boss_flash_timer -= 1

        if self.spawn_timer >= self.spawn_delay - 30:
            self.spawn_warning_timer = 30
        if self.spawn_warning_timer > 0:
            self.spawn_warning_timer -= 1

        self.bg_scroll_y = (self.bg_scroll_y + 2) % 40

    def display_frame(self, screen):
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-self.screen_shake, self.screen_shake)
            offset_y = random.randint(-self.screen_shake, self.screen_shake)

        if self.state == STATE_START:
            self.render_system.draw_start_screen(screen)
            return

        self.render_system.draw(screen, offset_x, offset_y)

    def reset_game(self):
        self.state = STATE_PLAYING

        self.all_sprites.empty()
        self.enemies.empty()
        self.projectiles.empty()
        self.gates.empty()
        self.gems.empty()
        self.powerups.empty()
        self.player_group.empty()

        self._create_player()

        self.wave_system.reset()
        self.upgrade_system.reset_progression()
        self.render_system.reset()
        self.particle_system.reset()

        self.combo_count = 0
        self.highest_combo = 0
        self.combo_multiplier = 1.0
        self.combo_pulse_timer = 0
        self.combo_just_increased = False

        self.screen_shake = 0
        self.bg_scroll_y = 0
        self.active_powerups = {}
        self._active_powerup_instances = {}
        self.boss_flash_timer = 0
        self.spawn_warning_timer = 0

    def check_collisions(self):
        self.collision_system.check_collisions()

    def trigger_win(self):
        self.state = STATE_WIN

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

    # External facade methods used by other gameplay entities.
    def spawn_explosion(self, x, y, count=10, color=(255, 0, 0)):
        self.particle_system.spawn_explosion(x, y, count=count, color=color)

    def spawn_death_explosion(self, x, y, enemy_type="small"):
        self.particle_system.spawn_death_explosion(x, y, enemy_type=enemy_type)

    def spawn_gold(self, x, y, amount=1):
        self.particle_system.spawn_gold(x, y, amount=amount)

    def spawn_gate_effect(self, x, y, positive=True):
        self.particle_system.spawn_gate_effect(x, y, positive=positive)

    def add_damage_text(self, x, y, value, color=None):
        self.render_system.add_damage_text(x, y, value, color=color)

    def add_gold_text(self, x, y, amount):
        self.render_system.add_gold_text(x, y, amount)

    def add_effect_text(self, x, y, text, positive=True):
        self.render_system.add_effect_text(x, y, text, positive=positive)
