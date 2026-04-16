from game.constants import (
    COMBO_TIER_1, COMBO_TIER_2, COMBO_TIER_3, COMBO_MULTIPLIERS
)


class ComboManager:
    def __init__(self):
        self.combo_count = 0
        self.highest_combo = 0
        self.multiplier = 1.0
        # Visual state
        self.pulse_timer = 0
        self.just_increased = False

    def register_kill(self):
        self.combo_count += 1
        self.just_increased = True
        self.pulse_timer = 15
        if self.combo_count > self.highest_combo:
            self.highest_combo = self.combo_count
        self._update_multiplier()

    def on_damage_taken(self):
        self.combo_count = 0
        self.multiplier = 1.0

    def _update_multiplier(self):
        if self.combo_count >= COMBO_TIER_3:
            self.multiplier = COMBO_MULTIPLIERS[COMBO_TIER_3]
        elif self.combo_count >= COMBO_TIER_2:
            self.multiplier = COMBO_MULTIPLIERS[COMBO_TIER_2]
        elif self.combo_count >= COMBO_TIER_1:
            self.multiplier = COMBO_MULTIPLIERS[COMBO_TIER_1]
        else:
            self.multiplier = 1.0

    def get_xp_multiplied(self, base_xp):
        return int(base_xp * self.multiplier)

    def update(self):
        if self.pulse_timer > 0:
            self.pulse_timer -= 1
        else:
            self.just_increased = False

    def reset(self):
        self.combo_count = 0
        self.highest_combo = 0
        self.multiplier = 1.0
        self.pulse_timer = 0
        self.just_increased = False
