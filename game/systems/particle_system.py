import math
import random

import pygame

from game.constants import GOLD_COLOR, GREEN, ORANGE, PARTICLE_CAP, RED, YELLOW, WHITE


class ParticleSystem:
    def __init__(self, game):
        self.game = game

    def reset(self):
        self.game.particles = []

    def spawn_explosion(self, x, y, count=10, color=RED):
        count = min(count, PARTICLE_CAP - len(self.game.particles))
        for _ in range(count):
            self.game.particles.append({
                "x": x,
                "y": y,
                "vx": random.uniform(-5, 5),
                "vy": random.uniform(-5, 5),
                "life": random.randint(20, 40),
                "color": color,
                "size": random.randint(2, 6),
                "gravity": 0.1,
            })

    def spawn_death_explosion(self, x, y, enemy_type="small"):
        base_count = {"small": 8, "medium": 14, "large": 22, "boss": 40}.get(enemy_type, 10)
        count = min(base_count, PARTICLE_CAP - len(self.game.particles))
        colors = [RED, ORANGE, YELLOW, WHITE]

        for _ in range(count):
            speed = random.uniform(2, 10)
            self.game.particles.append({
                "x": x,
                "y": y,
                "vx": random.uniform(-speed, speed),
                "vy": random.uniform(-speed, speed),
                "life": random.randint(15, 55),
                "color": random.choice(colors),
                "size": random.randint(3, 8),
                "gravity": 0.05,
            })

    def spawn_gold(self, x, y, amount=1):
        count = min(amount * 2, 10, PARTICLE_CAP - len(self.game.particles))
        for _ in range(count):
            self.game.particles.append({
                "x": x,
                "y": y,
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(-4, -1),
                "life": random.randint(20, 40),
                "color": GOLD_COLOR,
                "size": random.randint(2, 4),
                "gravity": 0.1,
            })

    def spawn_gate_effect(self, x, y, positive=True):
        count = min(20, PARTICLE_CAP - len(self.game.particles))
        color = GREEN if positive else RED

        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 5)
            self.game.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 50),
                "color": color,
                "size": random.randint(3, 6),
                "gravity": 0.0,
            })

    def spawn_bullet_trail(self, x, y, color=YELLOW):
        if len(self.game.particles) >= PARTICLE_CAP:
            return

        trail_color = (
            max(0, color[0] // 2),
            max(0, color[1] // 2),
            max(0, color[2] // 2),
        )
        self.game.particles.append({
            "x": x + random.uniform(-1, 1),
            "y": y + random.uniform(-1, 1),
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.3, 0.3),
            "life": random.randint(5, 12),
            "color": trail_color,
            "size": random.uniform(1.5, 3),
            "gravity": 0.0,
        })

    def update(self):
        for p in self.game.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += p.get("gravity", 0)
            p["life"] -= 1
            p["size"] = max(0, p["size"] - 0.05)
        self.game.particles = [p for p in self.game.particles if p["life"] > 0]

    def draw(self, screen, offset_x=0, offset_y=0):
        for p in self.game.particles:
            size = max(1, int(p["size"]))
            pygame.draw.circle(
                screen,
                p["color"],
                (int(p["x"] + offset_x), int(p["y"] + offset_y)),
                size,
            )
