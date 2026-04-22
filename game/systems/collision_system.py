import random

import pygame

from game.constants import (
    ENEMY_BOSS,
    POWERUP_DROP_CHANCE,
    POWERUP_DROP_ENEMIES,
    POWERUP_SHIELD,
    RED,
    XP_VALUES,
)
from game.powerup import PowerUp
from game.xp_gem import XPGem


class CollisionSystem:
    def __init__(self, game):
        self.game = game

    def check_collisions(self):
        game = self.game

        # Bullet -> Enemy
        hits = pygame.sprite.groupcollide(game.enemies, game.projectiles, False, False)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if bullet.alive():
                    bullet.collide(enemy, game)

            if enemy.health <= 0:
                gold = enemy.gold_value
                game.player.gold += gold
                game.add_gold_text(enemy.rect.centerx, enemy.rect.top - 15, gold)
                game.spawn_death_explosion(enemy.rect.centerx, enemy.rect.centery, enemy.enemy_type)
                game.spawn_gold(enemy.rect.centerx, enemy.rect.centery, gold)

                xp_val = XP_VALUES.get(enemy.enemy_type, 1)
                game.gems.add(XPGem(enemy.rect.centerx, enemy.rect.centery, xp_val))

                game._register_kill()

                if enemy.enemy_type == ENEMY_BOSS:
                    game.boss_flash_timer = 10
                    game.screen_shake = max(game.screen_shake, 12)

                game.screen_shake = max(game.screen_shake, 4)

                if enemy.enemy_type in POWERUP_DROP_ENEMIES and random.random() < POWERUP_DROP_CHANCE:
                    ptype = game.upgrade_system.random_drop_type()
                    game.powerups.add(PowerUp(enemy.rect.centerx, enemy.rect.centery, ptype))

                enemy.kill()

        # Gem -> Player
        collected_gems = pygame.sprite.spritecollide(game.player, game.gems, True)
        for gem in collected_gems:
            xp_gain = game._get_xp_multiplied(gem.xp_value)
            game.xp += xp_gain
            game.add_damage_text(
                game.player.rect.centerx,
                game.player.rect.top - 10,
                xp_gain,
                color=(0, 230, 64),
            )

        # PowerUp -> Player
        collected_powerups = pygame.sprite.spritecollide(game.player, game.powerups, False)
        for pu in collected_powerups:
            pu.collide(game.player, game)

        # Enemy -> Player
        player_hits = pygame.sprite.spritecollide(game.player, game.enemies, True)
        for enemy in player_hits:
            if POWERUP_SHIELD in game.active_powerups:
                game.spawn_explosion(
                    game.player.rect.centerx,
                    game.player.rect.centery,
                    count=15,
                    color=(100, 180, 255),
                )
                continue

            damage = enemy.damage
            game.player.health -= damage
            game._on_damage_taken()
            game.add_damage_text(game.player.rect.centerx, game.player.rect.top, -damage)
            game.screen_shake = max(game.screen_shake, 15)
            game.spawn_explosion(game.player.rect.centerx, game.player.rect.centery, count=20, color=RED)

            if game.player.health <= 0:
                game.player.health = 0
                game.player.dying = True
                game.player.set_animation_state("die")
            else:
                game.player.set_animation_state("hurt")

        # Player -> Gates
        gates_hit = pygame.sprite.spritecollide(game.player, game.gates, False)
        for gate in gates_hit:
            gate.collide(game.player, game)
