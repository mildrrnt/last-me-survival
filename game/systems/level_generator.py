import random
from game.entities.enemy import Zombie, Boss
from game.entities.gate import GateRow
from game.constants import (
    SCREEN_WIDTH, TOTAL_WAVES, WAVE_ENEMIES_BASE, GATE_INTERVAL_WAVES,
    ENEMY_SMALL, ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS,
    WAVE_TYPE_NORMAL, WAVE_TYPE_ELITE, WAVE_TYPE_SWARM,
    WAVE_TYPE_MIDBOSS, WAVE_TYPE_BLOOD_MOON, WAVE_TYPE_FINAL_BOSS
)


class LevelGenerator:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.spawn_timer = 0
        self.spawn_delay = 180  # Frames between waves (~3 seconds at 60fps)
        self.wave_number = 0
        self.total_waves = TOTAL_WAVES
        self.difficulty_factor = 0.0
        self.enemies_per_wave = WAVE_ENEMIES_BASE

        # Sub-wave spawning: each wave spawns enemies in bursts
        self.sub_wave_queue = []
        self.sub_wave_timer = 0
        self.sub_wave_delay = 25  # Frames between sub-wave bursts

        self.gate_timer = 0
        self.gate_delay = 400  # Frames between gate rows
        self.waves_since_gate = 0

        self.run_complete = False

        # Wave event state
        self.current_wave_type = WAVE_TYPE_NORMAL
        self.wave_announcement = ""
        self.announcement_timer = 0
        self.blood_moon_active = False

    @property
    def progress(self):
        return min(1.0, self.wave_number / self.total_waves)

    def classify_wave(self, wave_num):
        """Determine wave type based on wave number."""
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

    def update(self):
        if self.run_complete:
            # Drain remaining sub-wave enemies
            self._process_sub_wave()
            if len(self.sub_wave_queue) == 0 and len(self.game_manager.enemies) == 0:
                self.game_manager.trigger_win()
            return

        # Process sub-wave bursts (staggered enemy spawning within a wave)
        self._process_sub_wave()

        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.spawn_wave()

        self.gate_timer += 1
        if self.gate_timer >= self.gate_delay:
            self.gate_timer = 0
            self._spawn_gate_row()

        # Announcement timer
        if self.announcement_timer > 0:
            self.announcement_timer -= 1

    def _process_sub_wave(self):
        """Spawn queued enemies in staggered bursts."""
        if not self.sub_wave_queue:
            return
        self.sub_wave_timer += 1
        if self.sub_wave_timer >= self.sub_wave_delay:
            self.sub_wave_timer = 0
            # Spawn 1-2 enemies per burst
            burst = min(2, len(self.sub_wave_queue))
            for _ in range(burst):
                enemy_type = self.sub_wave_queue.pop(0)
                enemy = self._create_enemy(enemy_type)
                self.game_manager.enemies.add(enemy)
                self.game_manager.all_sprites.add(enemy)

    def _create_enemy(self, enemy_type):
        """Create the appropriate enemy instance based on type."""
        speed_bonus = self.difficulty_factor * 0.2
        hp_bonus = self.difficulty_factor * 5
        # Blood moon: all enemies faster
        if self.blood_moon_active:
            speed_bonus += 1.0

        if enemy_type == ENEMY_BOSS:
            enemy = Boss(
                speed_bonus=speed_bonus,
                hp_bonus=hp_bonus
            )
        else:
            enemy = Zombie(
                enemy_type=enemy_type,
                speed_bonus=speed_bonus,
                hp_bonus=hp_bonus
            )

        # Elite wave enemies get elite buff
        if self.current_wave_type == WAVE_TYPE_ELITE:
            enemy.set_elite()

        return enemy

    def spawn_wave(self):
        self.wave_number += 1
        self.waves_since_gate += 1

        # Classify wave type
        self.current_wave_type = self.classify_wave(self.wave_number)

        # Set announcement
        self._set_wave_announcement()

        # Handle special wave types
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
            # Normal wave
            composition = self._get_wave_composition()
            self.sub_wave_queue.extend(composition)

        # Scale difficulty — steeper late game
        if self.wave_number <= 20:
            self.difficulty_factor += 0.10
        else:
            self.difficulty_factor += 0.25
        self.enemies_per_wave = WAVE_ENEMIES_BASE + self.wave_number // 3

        # Waves get closer together over time
        if self.spawn_delay > 80:
            self.spawn_delay -= 3
        # Sub-wave bursts also speed up
        if self.sub_wave_delay > 12:
            self.sub_wave_delay -= 0.5

        # Gates at wave intervals
        if self.waves_since_gate >= GATE_INTERVAL_WAVES:
            self.waves_since_gate = 0
            self._spawn_gate_row()

    def _set_wave_announcement(self):
        """Set announcement text for special waves."""
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
            self.announcement_timer = 180  # 3 seconds
        else:
            # Show wave number briefly for normal waves
            self.wave_announcement = f"Wave {self.wave_number}"
            self.announcement_timer = 60

    def _get_wave_composition(self):
        """Determine what enemies to spawn based on current wave."""
        enemies = []
        count = min(self.enemies_per_wave + int(self.difficulty_factor), 15)

        for _ in range(count):
            roll = random.random()
            if self.wave_number <= 3:
                enemies.append(ENEMY_SMALL)
            elif self.wave_number <= 6:
                if roll < 0.5:
                    enemies.append(ENEMY_SMALL)
                else:
                    enemies.append(ENEMY_MEDIUM)
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
                # Late game: brutal mix
                if roll < 0.15:
                    enemies.append(ENEMY_MEDIUM)
                elif roll < 0.45:
                    enemies.append(ENEMY_LARGE)
                else:
                    enemies.append(ENEMY_BOSS)

        return enemies

    def _spawn_elite_wave(self):
        """Fewer but much tougher enemies with glow."""
        count = max(3, self.enemies_per_wave // 2)
        types = [ENEMY_MEDIUM, ENEMY_LARGE]
        for _ in range(count):
            enemy_type = random.choice(types)
            self.sub_wave_queue.append(enemy_type)

    def _spawn_swarm_wave(self):
        """Huge number of fast small enemies."""
        count = min(25, self.enemies_per_wave * 3)
        for _ in range(count):
            self.sub_wave_queue.append(ENEMY_SMALL)

    def _spawn_midboss_wave(self):
        """Wave 20: single massive enemy + minions."""
        # Queue boss first
        self.sub_wave_queue.append(ENEMY_BOSS)
        # Then minions
        for _ in range(6):
            roll = random.random()
            if roll < 0.5:
                self.sub_wave_queue.append(ENEMY_MEDIUM)
            else:
                self.sub_wave_queue.append(ENEMY_LARGE)

    def _spawn_blood_moon_wave(self):
        """Wave 30: red tint, all enemies faster (handled by blood_moon_active flag)."""
        count = min(18, self.enemies_per_wave * 2)
        types = [ENEMY_MEDIUM, ENEMY_LARGE, ENEMY_BOSS]
        for _ in range(count):
            self.sub_wave_queue.append(random.choice(types))

    def _spawn_final_boss_wave(self):
        """Wave 40: final boss with phase 2 reinforcements."""
        # Two mega bosses
        for _ in range(2):
            boss = Boss(
                speed_bonus=0.6,
                hp_bonus=self.difficulty_factor * 12
            )
            self.game_manager.enemies.add(boss)
            self.game_manager.all_sprites.add(boss)

        # Large minions
        for _ in range(5):
            e = Zombie(
                enemy_type=ENEMY_LARGE,
                speed_bonus=self.difficulty_factor * 0.15,
                hp_bonus=self.difficulty_factor * 4
            )
            self.game_manager.enemies.add(e)
            self.game_manager.all_sprites.add(e)

        # Medium reinforcements
        for _ in range(6):
            e = Zombie(
                enemy_type=ENEMY_MEDIUM,
                speed_bonus=self.difficulty_factor * 0.2,
                hp_bonus=self.difficulty_factor * 4
            )
            self.game_manager.enemies.add(e)
            self.game_manager.all_sprites.add(e)

    def _spawn_gate_row(self):
        num_gates = random.randint(2, 4)
        GateRow.spawn_gate_row(self.game_manager, num_gates)
