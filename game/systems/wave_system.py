from collections import deque
import random

from game.constants import (
    ENEMY_BOSS,
    ENEMY_LARGE,
    ENEMY_MEDIUM,
    ENEMY_SMALL,
    GATE_INTERVAL_WAVES,
    TOTAL_WAVES,
    WAVE_ENEMIES_BASE,
    WAVE_TYPE_BLOOD_MOON,
    WAVE_TYPE_ELITE,
    WAVE_TYPE_FINAL_BOSS,
    WAVE_TYPE_MIDBOSS,
    WAVE_TYPE_NORMAL,
    WAVE_TYPE_SWARM,
)
from game.enemy import Boss, Zombie
from game.gate import spawn_gate_row


class WaveSystem:
    def __init__(self, game):
        self.game = game

    def reset(self):
        game = self.game
        game.spawn_timer = 0
        game.spawn_delay = 180
        game.wave_number = 0
        game.total_waves = TOTAL_WAVES
        game.difficulty_factor = 0.0
        game.enemies_per_wave = WAVE_ENEMIES_BASE
        game.sub_wave_queue = deque()
        game.sub_wave_timer = 0
        game.sub_wave_delay = 25
        game.gate_timer = 0
        game.gate_delay = 400
        game.waves_since_gate = 0
        game.run_complete = False
        game.current_wave_type = WAVE_TYPE_NORMAL
        game.wave_announcement = ""
        game.announcement_timer = 0
        game.blood_moon_active = False

    def update(self):
        game = self.game
        if game.run_complete:
            self._process_sub_wave()
            if not game.sub_wave_queue and not game.enemies:
                game.trigger_win()
            return

        self._process_sub_wave()

        game.spawn_timer += 1
        if game.spawn_timer >= game.spawn_delay:
            game.spawn_timer = 0
            self._spawn_wave()

        game.gate_timer += 1
        if game.gate_timer >= game.gate_delay:
            game.gate_timer = 0
            spawn_gate_row(game, random.randint(2, 4))

        if game.announcement_timer > 0:
            game.announcement_timer -= 1

    def _process_sub_wave(self):
        game = self.game
        if not game.sub_wave_queue:
            return

        game.sub_wave_timer += 1
        if game.sub_wave_timer < game.sub_wave_delay:
            return

        game.sub_wave_timer = 0
        burst = min(2, len(game.sub_wave_queue))
        for _ in range(burst):
            enemy_type = game.sub_wave_queue.popleft()
            enemy = self._create_enemy(enemy_type)
            game.enemies.add(enemy)
            game.all_sprites.add(enemy)

    def _create_enemy(self, enemy_type):
        game = self.game
        speed_bonus = game.difficulty_factor * 0.2
        hp_bonus = game.difficulty_factor * 5
        if game.blood_moon_active:
            speed_bonus += 1.0

        if enemy_type == ENEMY_BOSS:
            enemy = Boss(speed_bonus=speed_bonus, hp_bonus=hp_bonus)
        else:
            enemy = Zombie(enemy_type=enemy_type, speed_bonus=speed_bonus, hp_bonus=hp_bonus)

        if game.current_wave_type == WAVE_TYPE_ELITE:
            enemy.set_elite()

        return enemy

    def _spawn_wave(self):
        game = self.game
        game.wave_number += 1
        game.waves_since_gate += 1
        game.current_wave_type = self._classify_wave(game.wave_number)
        self._set_wave_announcement()

        if game.current_wave_type == WAVE_TYPE_FINAL_BOSS:
            game.run_complete = True
            self._spawn_final_boss_wave()
            return

        if game.current_wave_type == WAVE_TYPE_MIDBOSS:
            self._spawn_midboss_wave()
        elif game.current_wave_type == WAVE_TYPE_BLOOD_MOON:
            game.blood_moon_active = True
            self._spawn_blood_moon_wave()
        elif game.current_wave_type == WAVE_TYPE_SWARM:
            self._spawn_swarm_wave()
        elif game.current_wave_type == WAVE_TYPE_ELITE:
            self._spawn_elite_wave()
        else:
            game.sub_wave_queue.extend(self._get_wave_composition())

        game.difficulty_factor += 0.10 if game.wave_number <= 20 else 0.25
        game.enemies_per_wave = WAVE_ENEMIES_BASE + game.wave_number // 3

        if game.spawn_delay > 80:
            game.spawn_delay -= 3
        if game.sub_wave_delay > 12:
            game.sub_wave_delay -= 0.5

        if game.waves_since_gate >= GATE_INTERVAL_WAVES:
            game.waves_since_gate = 0
            spawn_gate_row(game, random.randint(2, 4))

    @staticmethod
    def _classify_wave(wave_num):
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
        game = self.game
        announcements = {
            WAVE_TYPE_ELITE: "ELITE WAVE",
            WAVE_TYPE_SWARM: "SWARM!",
            WAVE_TYPE_MIDBOSS: "MID-BOSS!",
            WAVE_TYPE_BLOOD_MOON: "BLOOD MOON",
            WAVE_TYPE_FINAL_BOSS: "FINAL BOSS",
        }
        text = announcements.get(game.current_wave_type, "")
        if text:
            game.wave_announcement = text
            game.announcement_timer = 180
        else:
            game.wave_announcement = f"Wave {game.wave_number}"
            game.announcement_timer = 60

    def _get_wave_composition(self):
        game = self.game
        enemies = []
        count = min(game.enemies_per_wave + int(game.difficulty_factor), 15)
        for _ in range(count):
            roll = random.random()
            if game.wave_number <= 3:
                enemies.append(ENEMY_SMALL)
            elif game.wave_number <= 6:
                enemies.append(ENEMY_SMALL if roll < 0.5 else ENEMY_MEDIUM)
            elif game.wave_number <= 12:
                if roll < 0.20:
                    enemies.append(ENEMY_SMALL)
                elif roll < 0.55:
                    enemies.append(ENEMY_MEDIUM)
                else:
                    enemies.append(ENEMY_LARGE)
            elif game.wave_number <= 25:
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
        game = self.game
        count = max(3, game.enemies_per_wave // 2)
        for _ in range(count):
            game.sub_wave_queue.append(random.choice([ENEMY_MEDIUM, ENEMY_LARGE]))

    def _spawn_swarm_wave(self):
        game = self.game
        count = min(25, game.enemies_per_wave * 3)
        for _ in range(count):
            game.sub_wave_queue.append(ENEMY_SMALL)

    def _spawn_midboss_wave(self):
        game = self.game
        game.sub_wave_queue.append(ENEMY_BOSS)
        for _ in range(6):
            game.sub_wave_queue.append(ENEMY_MEDIUM if random.random() < 0.5 else ENEMY_LARGE)

    def _spawn_blood_moon_wave(self):
        game = self.game
        count = min(18, game.enemies_per_wave * 2)
        for _ in range(count):
            game.sub_wave_queue.append(random.choice([ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS]))

    def _spawn_final_boss_wave(self):
        game = self.game
        for _ in range(2):
            boss = Boss(speed_bonus=0.6, hp_bonus=game.difficulty_factor * 12)
            game.enemies.add(boss)
            game.all_sprites.add(boss)

        for _ in range(5):
            enemy = Zombie(
                enemy_type=ENEMY_LARGE,
                speed_bonus=game.difficulty_factor * 0.15,
                hp_bonus=game.difficulty_factor * 4,
            )
            game.enemies.add(enemy)
            game.all_sprites.add(enemy)

        for _ in range(6):
            enemy = Zombie(
                enemy_type=ENEMY_MEDIUM,
                speed_bonus=game.difficulty_factor * 0.2,
                hp_bonus=game.difficulty_factor * 4,
            )
            game.enemies.add(enemy)
            game.all_sprites.add(enemy)
