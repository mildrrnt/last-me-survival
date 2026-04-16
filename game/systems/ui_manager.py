import pygame
import math
from game.constants import (
    WHITE, RED, BLACK, GREEN, YELLOW, ORANGE, GRAY, DARK_GRAY,
    SCREEN_WIDTH, SCREEN_HEIGHT, GOLD_COLOR,
    POWERUP_COLORS, POWERUP_LABELS, POWERUP_DURATIONS,
    COMBO_TIER_1,
    WAVE_TYPE_ELITE, WAVE_TYPE_SWARM, WAVE_TYPE_MIDBOSS,
    WAVE_TYPE_BLOOD_MOON, WAVE_TYPE_FINAL_BOSS
)


class UIManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.font_small = pygame.font.SysFont(None, 20)
        self.font_medium = pygame.font.SysFont(None, 28)
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_xl = pygame.font.SysFont(None, 64)
        self.floating_texts = []

    def add_damage_text(self, x, y, value, color=None):
        if color is None:
            color = RED if value < 0 else WHITE
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': str(abs(value)) if value >= 0 else str(value),
            'timer': 45,
            'color': color,
            'scale': 1.0
        })

    def add_gold_text(self, x, y, amount):
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': f"+{amount}",
            'timer': 40,
            'color': GOLD_COLOR,
            'scale': 0.8
        })

    def add_effect_text(self, x, y, text, positive=True):
        color = GREEN if positive else RED
        self.floating_texts.append({
            'x': x, 'y': y,
            'text': text,
            'timer': 60,
            'color': color,
            'scale': 1.2
        })

    def update(self):
        for ft in self.floating_texts:
            ft['y'] -= 1.2
            ft['timer'] -= 1
        self.floating_texts = [ft for ft in self.floating_texts if ft['timer'] > 0]

    def draw(self, screen):
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
            font = self.font_medium
            text_surf = font.render(ft['text'], True, ft['color'])
            # Fade effect via alpha
            if ft['timer'] < 15:
                text_surf.set_alpha(alpha)
            screen.blit(text_surf, (ft['x'] - text_surf.get_width() // 2, ft['y']))

    def _draw_health_bar(self, screen):
        player = self.game_manager.player
        bar_w = 160
        bar_h = 16
        x, y = 10, 10

        # Background
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        # Fill
        fill = max(0, int(bar_w * (player.health / player.max_health)))
        fill_color = GREEN if player.health > 50 else ORANGE if player.health > 25 else RED
        pygame.draw.rect(screen, fill_color, (x, y, fill, bar_h), border_radius=3)
        # Border
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 2, border_radius=3)
        # HP text
        hp_text = self.font_small.render(f"{player.health}/{player.max_health}", True, WHITE)
        screen.blit(hp_text, (x + bar_w // 2 - hp_text.get_width() // 2, y + 1))

    def _draw_gold(self, screen):
        player = self.game_manager.player
        gold_text = self.font_medium.render(f"{player.gold}", True, GOLD_COLOR)
        # Gold icon (small circle)
        icon_x = SCREEN_WIDTH - 10 - gold_text.get_width() - 22
        icon_y = 12
        pygame.draw.circle(screen, GOLD_COLOR, (icon_x + 8, icon_y + 8), 8)
        pygame.draw.circle(screen, (200, 170, 0), (icon_x + 8, icon_y + 8), 8, 2)
        g_surf = self.font_small.render("G", True, BLACK)
        screen.blit(g_surf, (icon_x + 3, icon_y + 2))
        screen.blit(gold_text, (icon_x + 20, icon_y))

    def _draw_power_indicator(self, screen):
        player = self.game_manager.player
        power = player.power
        # Power badge
        x, y = 10, 32
        label = self.font_small.render("PWR", True, GRAY)
        screen.blit(label, (x, y))
        value = self.font_medium.render(str(power), True, YELLOW)
        screen.blit(value, (x + 35, y - 2))

    def _draw_wave_progress(self, screen):
        gm = self.game_manager
        progress = gm.level_generator.progress
        wave = gm.level_generator.wave_number
        total = gm.level_generator.total_waves

        # Progress bar at top-center
        bar_w = 140
        bar_h = 10
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 6

        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        fill = int(bar_w * progress)
        pygame.draw.rect(screen, (100, 200, 255), (x, y, fill, bar_h), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 1, border_radius=3)

        wave_text = self.font_small.render(f"Wave {min(wave, total)}/{total}", True, WHITE)
        screen.blit(wave_text, (x + bar_w // 2 - wave_text.get_width() // 2, y + 12))

    def _draw_weapon_name(self, screen):
        player = self.game_manager.player
        weapon = player.weapon
        text = self.font_small.render(weapon.name, True, weapon.color)
        screen.blit(text, (10, 52))

    def _draw_combo_counter(self, screen):
        combo = self.game_manager.combo_manager
        if combo.combo_count < COMBO_TIER_1:
            return

        # Position: right side, below gold
        x = SCREEN_WIDTH - 10
        y = 36

        # Pulse/shake effect
        shake_x = 0
        shake_y = 0
        if combo.just_increased:
            shake_x = int(math.sin(combo.pulse_timer * 2) * 3)
            shake_y = int(math.cos(combo.pulse_timer * 3) * 2)

        # Multiplier color
        if combo.multiplier >= 3.0:
            color = RED
        elif combo.multiplier >= 2.0:
            color = ORANGE
        else:
            color = YELLOW

        # Combo count
        combo_text = self.font_medium.render(f"x{combo.combo_count}", True, color)
        screen.blit(combo_text, (x - combo_text.get_width() + shake_x, y + shake_y))

        # Multiplier text below
        mult_text = self.font_small.render(f"{combo.multiplier}x XP", True, color)
        screen.blit(mult_text, (x - mult_text.get_width() + shake_x, y + 22 + shake_y))

    def _draw_powerup_timers(self, screen):
        active = self.game_manager.active_powerups
        if not active:
            return

        # Draw timer bars on the left, below weapon name
        y_offset = 70
        bar_w = 80
        bar_h = 10

        for ptype, remaining in active.items():
            color = POWERUP_COLORS.get(ptype, WHITE)
            label = POWERUP_LABELS.get(ptype, "???")
            max_dur = POWERUP_DURATIONS.get(ptype, 5.0)

            # Label
            lbl = self.font_small.render(label, True, color)
            screen.blit(lbl, (10, y_offset))

            # Bar background
            bar_y = y_offset + 14
            pygame.draw.rect(screen, DARK_GRAY, (10, bar_y, bar_w, bar_h), border_radius=2)
            # Fill
            fill = max(0, int(bar_w * (remaining / max_dur)))
            pygame.draw.rect(screen, color, (10, bar_y, fill, bar_h), border_radius=2)
            pygame.draw.rect(screen, WHITE, (10, bar_y, bar_w, bar_h), 1, border_radius=2)

            y_offset += 28

    def _draw_wave_announcement(self, screen):
        lg = self.game_manager.level_generator
        if lg.announcement_timer <= 0 or not lg.wave_announcement:
            return

        # Pick color based on wave type
        color_map = {
            WAVE_TYPE_ELITE: GOLD_COLOR,
            WAVE_TYPE_SWARM: WHITE,
            WAVE_TYPE_MIDBOSS: RED,
            WAVE_TYPE_BLOOD_MOON: (200, 30, 30),
            WAVE_TYPE_FINAL_BOSS: RED,
        }
        color = color_map.get(lg.current_wave_type, (180, 180, 180))

        # Fade in/out
        if lg.announcement_timer > 150:
            alpha = int(255 * ((180 - lg.announcement_timer) / 30))
        elif lg.announcement_timer < 30:
            alpha = int(255 * (lg.announcement_timer / 30))
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))

        # Render text
        if lg.current_wave_type in color_map:
            font = self.font_xl
        else:
            font = self.font_large

        text_surf = font.render(lg.wave_announcement, True, color)
        text_surf.set_alpha(alpha)

        x = SCREEN_WIDTH // 2 - text_surf.get_width() // 2
        y = SCREEN_HEIGHT // 3
        screen.blit(text_surf, (x, y))

    def _draw_xp_bar(self, screen):
        gm = self.game_manager
        if gm.xp_to_next_level <= 0:
            return

        bar_w = 100
        bar_h = 6
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 28

        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=2)
        fill = int(bar_w * min(1.0, gm.xp / gm.xp_to_next_level))
        pygame.draw.rect(screen, (0, 230, 64), (x, y, fill, bar_h), border_radius=2)
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_w, bar_h), 1, border_radius=2)

    def draw_start_screen(self, screen):
        # Dim overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 20, 30))
        screen.blit(overlay, (0, 0))

        # Title
        title = self.font_xl.render("LAST Z SURVIVAL", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))

        # Subtitle
        sub = self.font_medium.render("Survive the zombie horde!", True, GRAY)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 280))

        # Instructions
        instr = self.font_medium.render("Press SPACE to Start", True, WHITE)
        # Blink effect
        tick = pygame.time.get_ticks()
        if (tick // 500) % 2 == 0:
            screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, 450))

        # Controls
        ctrl1 = self.font_small.render("A/D or Arrow Keys to Move", True, GRAY)
        ctrl2 = self.font_small.render("Auto-fire at nearest zombie", True, GRAY)
        ctrl3 = self.font_small.render("Choose gates wisely!", True, GRAY)
        screen.blit(ctrl1, (SCREEN_WIDTH // 2 - ctrl1.get_width() // 2, 530))
        screen.blit(ctrl2, (SCREEN_WIDTH // 2 - ctrl2.get_width() // 2, 555))
        screen.blit(ctrl3, (SCREEN_WIDTH // 2 - ctrl3.get_width() // 2, 580))

    def draw_game_over(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render("GAME OVER", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        player = self.game_manager.player
        wave = self.game_manager.level_generator.wave_number
        stats = self.font_medium.render(f"Wave {wave}  |  Gold: {player.gold}", True, GOLD_COLOR)
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))

        # Show highest combo
        best_combo = self.game_manager.combo_manager.highest_combo
        if best_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {best_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        restart = self.font_medium.render("Press R to Restart", True, WHITE)
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    def draw_win_screen(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 20, 0))
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render("SURVIVED!", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        player = self.game_manager.player
        stats = self.font_medium.render(f"Gold: {player.gold}  |  Power: {player.power}", True, GOLD_COLOR)
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))

        sub = self.font_medium.render("You cleared all 40 waves!", True, WHITE)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        # Show highest combo
        best_combo = self.game_manager.combo_manager.highest_combo
        if best_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {best_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

        restart = self.font_medium.render("Press R to Play Again", True, WHITE)
        screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, SCREEN_HEIGHT // 2 + 90))
