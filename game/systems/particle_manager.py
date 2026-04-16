import pygame
import random
import math
from game.constants import RED, YELLOW, WHITE, ORANGE, GREEN, GOLD_COLOR, PARTICLE_CAP


class ParticleManager:
    def __init__(self):
        self.particles = []

    def _can_spawn(self, count=1):
        """Check if we can add more particles without exceeding cap."""
        return len(self.particles) + count <= PARTICLE_CAP

    def spawn_explosion(self, x, y, count=10, color=RED):
        count = min(count, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
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

    def spawn_blood(self, x, y):
        count = min(8, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-4, 4),
                'vy': random.uniform(-6, -1),
                'life': random.randint(15, 35),
                'color': RED,
                'size': random.randint(2, 5),
                'gravity': 0.15
            })

    def spawn_death_explosion(self, x, y, enemy_type="small"):
        """Big explosion on enemy death — bigger than before."""
        base_count = {
            "small": 8, "medium": 14, "large": 22, "boss": 40,
            "charger": 16, "splitter": 12
        }.get(enemy_type, 10)
        count = min(base_count, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
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

    def spawn_confetti(self, x, y):
        count = min(15, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
        colors = [RED, YELLOW, WHITE, GREEN, (0, 100, 255)]
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-8, -2),
                'life': random.randint(40, 80),
                'color': random.choice(colors),
                'size': random.randint(3, 5),
                'gravity': 0.08
            })

    def spawn_gold(self, x, y, amount=1):
        """Spawn gold pickup particles."""
        desired = min(amount * 2, 10)
        count = min(desired, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
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
        """Visual feedback for gate pickup."""
        count = min(20, PARTICLE_CAP - len(self.particles))
        if count <= 0:
            return
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
        """Spawn fading trail particles behind projectiles."""
        if len(self.particles) >= PARTICLE_CAP:
            return
        # Dim the color for the trail
        trail_color = (
            max(0, color[0] // 2),
            max(0, color[1] // 2),
            max(0, color[2] // 2)
        )
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

    def update(self):
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += p.get('gravity', 0)
            p['life'] -= 1
            p['size'] = max(0, p['size'] - 0.05)

        self.particles = [p for p in self.particles if p['life'] > 0]

    def draw(self, screen, offset_x=0, offset_y=0):
        for p in self.particles:
            size = max(1, int(p['size']))
            x = int(p['x'] + offset_x)
            y = int(p['y'] + offset_y)
            pygame.draw.circle(screen, p['color'], (x, y), size)
