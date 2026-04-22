import math

import pygame

from game.constants import (
    BLACK,
    COMBO_TIER_1,
    DARK_GRAY,
    GOLD_COLOR,
    GRAY,
    GREEN,
    ORANGE,
    POWERUP_COLORS,
    POWERUP_DURATIONS,
    POWERUP_LABELS,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STATE_GAMEOVER,
    STATE_PAUSE,
    STATE_PLAYING,
    STATE_UPGRADE,
    STATE_WIN,
    WHITE,
    WAVE_TYPE_BLOOD_MOON,
    WAVE_TYPE_ELITE,
    WAVE_TYPE_FINAL_BOSS,
    WAVE_TYPE_MIDBOSS,
    WAVE_TYPE_SWARM,
    YELLOW,
)
from game.gate import draw_lane_dividers


class RenderSystem:
    def __init__(self, game):
        self.game = game
        self.font_small = pygame.font.SysFont(None, 20)
        self.font_medium = pygame.font.SysFont(None, 28)
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_xl = pygame.font.SysFont(None, 64)
        self.font_card = pygame.font.SysFont(None, 26)
        self.font_desc = pygame.font.SysFont(None, 20)
        self.floating_texts = []
        self._glow_cache = {}

    def reset(self):
        self.floating_texts = []

    def update_floating_texts(self):
        for ft in self.floating_texts:
            ft["y"] -= 1.2
            ft["timer"] -= 1
        self.floating_texts = [ft for ft in self.floating_texts if ft["timer"] > 0]

    def add_damage_text(self, x, y, value, color=None):
        if color is None:
            color = RED if value < 0 else WHITE
        self.floating_texts.append({
            "x": x,
            "y": y,
            "text": str(abs(value)) if value >= 0 else str(value),
            "timer": 45,
            "color": color,
        })

    def add_gold_text(self, x, y, amount):
        self.floating_texts.append({
            "x": x,
            "y": y,
            "text": f"+{amount}",
            "timer": 40,
            "color": GOLD_COLOR,
        })

    def add_effect_text(self, x, y, text, positive=True):
        self.floating_texts.append({
            "x": x,
            "y": y,
            "text": text,
            "timer": 60,
            "color": GREEN if positive else RED,
        })

    def draw(self, screen, offset_x, offset_y):
        game = self.game
        self._draw_background(screen, offset_x, offset_y)

        if game.blood_moon_active:
            tint = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            tint.fill((138, 7, 7, 35))
            screen.blit(tint, (0, 0))

        if game.gates:
            draw_lane_dividers(screen, 0, SCREEN_HEIGHT, offset_x, offset_y)

        for sprite in game.all_sprites:
            screen.blit(sprite.image, (sprite.rect.x + offset_x, sprite.rect.y + offset_y))

        for gem in game.gems:
            screen.blit(gem.image, (gem.rect.x + offset_x, gem.rect.y + offset_y))

        for pu in game.powerups:
            screen.blit(pu.image, (pu.rect.x + offset_x, pu.rect.y + offset_y))

        for enemy in game.enemies:
            enemy.draw_health_bar(screen, offset_x, offset_y)

        if game.active_powerups and game.state == STATE_PLAYING:
            self._draw_player_glow(screen, offset_x, offset_y)

        game.particle_system.draw(screen, offset_x, offset_y)

        if game.boss_flash_timer > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int(200 * (game.boss_flash_timer / 10))
            flash.fill((255, 255, 255, alpha))
            screen.blit(flash, (0, 0))

        if game.spawn_warning_timer > 0:
            warn_alpha = int(120 * (game.spawn_warning_timer / 30))
            warn_surf = pygame.Surface((SCREEN_WIDTH, 6), pygame.SRCALPHA)
            warn_surf.fill((255, 50, 50, warn_alpha))
            screen.blit(warn_surf, (0, 0))

        self._draw_ui(screen)

        if game.state == STATE_GAMEOVER:
            self._draw_game_over(screen)
        elif game.state == STATE_WIN:
            self._draw_win_screen(screen)
        elif game.state == STATE_UPGRADE:
            self._draw_upgrade_cards(screen)
        elif game.state == STATE_PAUSE:
            self._draw_pause_screen(screen)

    def draw_start_screen(self, screen):
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

        lines = ["A/D or Arrow Keys to Move", "Auto-fire at nearest zombie", "Choose gates wisely!"]
        for i, line in enumerate(lines):
            surf = self.font_small.render(line, True, GRAY)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, 530 + i * 25))

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
            alpha = min(255, ft["timer"] * 8)
            text_surf = self.font_medium.render(ft["text"], True, ft["color"])
            if ft["timer"] < 15:
                text_surf.set_alpha(alpha)
            screen.blit(text_surf, (ft["x"] - text_surf.get_width() // 2, ft["y"]))

    def _draw_health_bar(self, screen):
        game = self.game
        bar_w, bar_h = 160, 16
        x, y = 10, 10
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        fill = max(0, int(bar_w * (game.player.health / game.player.max_health)))
        fill_color = GREEN if game.player.health > 50 else ORANGE if game.player.health > 25 else RED
        pygame.draw.rect(screen, fill_color, (x, y, fill, bar_h), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 2, border_radius=3)
        hp_text = self.font_small.render(f"{game.player.health}/{game.player.max_health}", True, WHITE)
        screen.blit(hp_text, (x + bar_w // 2 - hp_text.get_width() // 2, y + 1))

    def _draw_gold(self, screen):
        game = self.game
        gold_text = self.font_medium.render(f"{game.player.gold}", True, GOLD_COLOR)
        icon_x = SCREEN_WIDTH - 10 - gold_text.get_width() - 22
        icon_y = 12
        pygame.draw.circle(screen, GOLD_COLOR, (icon_x + 8, icon_y + 8), 8)
        pygame.draw.circle(screen, (200, 170, 0), (icon_x + 8, icon_y + 8), 8, 2)
        g_surf = self.font_small.render("G", True, BLACK)
        screen.blit(g_surf, (icon_x + 3, icon_y + 2))
        screen.blit(gold_text, (icon_x + 20, icon_y))

    def _draw_power_indicator(self, screen):
        game = self.game
        x, y = 10, 32
        label = self.font_small.render("PWR", True, GRAY)
        screen.blit(label, (x, y))
        value = self.font_medium.render(str(game.player.power), True, YELLOW)
        screen.blit(value, (x + 35, y - 2))

    def _draw_wave_progress(self, screen):
        game = self.game
        progress = min(1.0, game.wave_number / game.total_waves)
        bar_w, bar_h = 140, 10
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 6
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, (100, 200, 255), (x, y, int(bar_w * progress), bar_h), border_radius=3)
        pygame.draw.rect(screen, WHITE, (x, y, bar_w, bar_h), 1, border_radius=3)
        wave_text = self.font_small.render(
            f"Wave {min(game.wave_number, game.total_waves)}/{game.total_waves}",
            True,
            WHITE,
        )
        screen.blit(wave_text, (x + bar_w // 2 - wave_text.get_width() // 2, y + 12))

    def _draw_weapon_name(self, screen):
        self.game.player.weapon.draw(screen, 10, 52)

    def _draw_combo_counter(self, screen):
        game = self.game
        if game.combo_count < COMBO_TIER_1:
            return

        x, y = SCREEN_WIDTH - 10, 36
        shake_x = shake_y = 0
        if game.combo_just_increased:
            shake_x = int(math.sin(game.combo_pulse_timer * 2) * 3)
            shake_y = int(math.cos(game.combo_pulse_timer * 3) * 2)

        color = RED if game.combo_multiplier >= 3.0 else ORANGE if game.combo_multiplier >= 2.0 else YELLOW
        combo_text = self.font_medium.render(f"x{game.combo_count}", True, color)
        screen.blit(combo_text, (x - combo_text.get_width() + shake_x, y + shake_y))

        mult_text = self.font_small.render(f"{game.combo_multiplier}x XP", True, color)
        screen.blit(mult_text, (x - mult_text.get_width() + shake_x, y + 22 + shake_y))

    def _draw_powerup_timers(self, screen):
        game = self.game
        if not game.active_powerups:
            return

        y_offset = 70
        bar_w, bar_h = 80, 10
        for ptype, remaining in game.active_powerups.items():
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
        game = self.game
        if game.announcement_timer <= 0 or not game.wave_announcement:
            return

        color_map = {
            WAVE_TYPE_ELITE: GOLD_COLOR,
            WAVE_TYPE_SWARM: WHITE,
            WAVE_TYPE_MIDBOSS: RED,
            WAVE_TYPE_BLOOD_MOON: (200, 30, 30),
            WAVE_TYPE_FINAL_BOSS: RED,
        }
        color = color_map.get(game.current_wave_type, (180, 180, 180))

        if game.announcement_timer > 150:
            alpha = int(255 * ((180 - game.announcement_timer) / 30))
        elif game.announcement_timer < 30:
            alpha = int(255 * (game.announcement_timer / 30))
        else:
            alpha = 255

        alpha = max(0, min(255, alpha))
        font = self.font_xl if game.current_wave_type in color_map else self.font_large
        text_surf = font.render(game.wave_announcement, True, color)
        text_surf.set_alpha(alpha)
        screen.blit(text_surf, (SCREEN_WIDTH // 2 - text_surf.get_width() // 2, SCREEN_HEIGHT // 3))

    def _draw_xp_bar(self, screen):
        game = self.game
        if game.xp_to_next_level <= 0:
            return

        bar_w, bar_h = 100, 6
        x = SCREEN_WIDTH // 2 - bar_w // 2
        y = 28
        pygame.draw.rect(screen, DARK_GRAY, (x, y, bar_w, bar_h), border_radius=2)
        fill = int(bar_w * min(1.0, game.xp / game.xp_to_next_level))
        pygame.draw.rect(screen, (0, 230, 64), (x, y, fill, bar_h), border_radius=2)
        pygame.draw.rect(screen, (100, 100, 100), (x, y, bar_w, bar_h), 1, border_radius=2)

    def _draw_upgrade_cards(self, screen):
        game = self.game
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_large.render("Choose Upgrade", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        mouse_pos = pygame.mouse.get_pos()
        for card in game.upgrade_cards:
            rect = card["rect"]
            hovered = rect.collidepoint(mouse_pos)
            card["hover"] = hovered

            bg_color = (80, 80, 110) if hovered else (60, 60, 80)
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)

            icon_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, 50)
            icon_color = card["data"].get("icon_color", (80, 80, 120))
            pygame.draw.rect(screen, icon_color, icon_rect, border_radius=4)

            text = self.font_card.render(card["data"]["text"], True, WHITE)
            screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + 70))

            desc = self.font_desc.render(card["data"]["desc"], True, GRAY)
            screen.blit(desc, (rect.x + rect.width // 2 - desc.get_width() // 2, rect.y + 100))

            border_color = YELLOW if hovered else WHITE
            pygame.draw.rect(screen, border_color, rect, 3 if hovered else 2, border_radius=8)

    def _draw_end_buttons(self, screen):
        game = self.game
        mouse_pos = pygame.mouse.get_pos()
        for rect, label in ((game.end_restart_rect, "Restart"), (game.end_home_rect, "Home")):
            hovered = rect.collidepoint(mouse_pos)
            bg = (80, 80, 110) if hovered else (60, 60, 80)
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, YELLOW if hovered else WHITE, rect, 3 if hovered else 2, border_radius=6)
            text_surf = self.font_medium.render(label, True, WHITE)
            screen.blit(
                text_surf,
                (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2),
            )

    def _draw_pause_screen(self, screen):
        game = self.game
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render("PAUSED", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 200))

        stats = [
            (f"HP: {game.player.health}/{game.player.max_health}", GREEN),
            (f"Power: {game.player.power}", YELLOW),
            (f"Coin: {game.player.gold}", GOLD_COLOR),
        ]
        for i, (text, color) in enumerate(stats):
            surf = self.font_medium.render(text, True, color)
            screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, SCREEN_HEIGHT // 2 - 120 + i * 32))

        mouse_pos = pygame.mouse.get_pos()
        for rect, label in ((game.pause_resume_rect, "Resume"), (game.pause_resign_rect, "Resign")):
            hovered = rect.collidepoint(mouse_pos)
            bg = (80, 80, 110) if hovered else (60, 60, 80)
            pygame.draw.rect(screen, bg, rect, border_radius=6)
            pygame.draw.rect(screen, YELLOW if hovered else WHITE, rect, 3 if hovered else 2, border_radius=6)
            text_surf = self.font_medium.render(label, True, WHITE)
            screen.blit(
                text_surf,
                (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2),
            )

    def _draw_game_over(self, screen):
        game = self.game
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render("GAME OVER", True, RED)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        stats = self.font_medium.render(
            f"Wave {game.wave_number}  |  Gold: {game.player.gold}",
            True,
            GOLD_COLOR,
        )
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))

        if game.highest_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {game.highest_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        self._draw_end_buttons(screen)

    def _draw_win_screen(self, screen):
        game = self.game
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 20, 0))
        screen.blit(overlay, (0, 0))

        title = self.font_xl.render("SURVIVED!", True, GREEN)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 80))

        stats = self.font_medium.render(
            f"Gold: {game.player.gold}  |  Power: {game.player.power}",
            True,
            GOLD_COLOR,
        )
        screen.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, SCREEN_HEIGHT // 2 - 10))

        sub = self.font_medium.render("You cleared all 40 waves!", True, WHITE)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        if game.highest_combo >= COMBO_TIER_1:
            combo_stat = self.font_small.render(f"Best Combo: {game.highest_combo}", True, YELLOW)
            screen.blit(combo_stat, (SCREEN_WIDTH // 2 - combo_stat.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

        self._draw_end_buttons(screen)

    def _draw_background(self, screen, offset_x, offset_y):
        game = self.game
        screen.fill((35, 35, 45))
        grid_color = (45, 45, 55)
        grid_spacing = 40

        for y in range(-grid_spacing, SCREEN_HEIGHT + grid_spacing, grid_spacing):
            py = y + (game.bg_scroll_y % grid_spacing) + offset_y
            pygame.draw.line(screen, grid_color, (0, py), (SCREEN_WIDTH, py))

        for x in range(0, SCREEN_WIDTH + grid_spacing, grid_spacing):
            px = x + offset_x
            pygame.draw.line(screen, grid_color, (px, 0), (px, SCREEN_HEIGHT))

        pygame.draw.rect(screen, (40, 40, 52), (30 + offset_x, 0, SCREEN_WIDTH - 60, SCREEN_HEIGHT))

    def _draw_player_glow(self, screen, offset_x, offset_y):
        game = self.game
        for ptype in game.active_powerups:
            color = POWERUP_COLORS.get(ptype, (255, 255, 255))
            glow_surf = self._glow_cache.get(ptype)
            if glow_surf is None:
                glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 50), (25, 25), 25)
                self._glow_cache[ptype] = glow_surf

            x = game.player.rect.centerx - 25 + offset_x
            y = game.player.rect.centery - 25 + offset_y
            screen.blit(glow_surf, (x, y))
            break
