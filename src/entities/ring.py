from src.utils.vector import Vector2
from src.config import CONFIG
from src.entities.particle import Particle
import pygame
import random
import math
from typing import List, Tuple

class Ring:
    def __init__(self, center: Vector2, radius: float, rotation: float, 
                 gap_size: float, color: Tuple[int, int, int]):
        self.center = center
        self.radius = radius
        self.rotation = rotation
        self.gap_size = gap_size
        self.destroyed = False
        self.particles: List[Particle] = []
        self.destruction_particles = 100
        self.color = color
        self.thickness = CONFIG['thickness']
        self.gap_tolerance = 0.1
        self.force_display = False
        self.two_pi = 2 * math.pi
    
    def create_destruction_particles(self):
        for _ in range(self.destruction_particles):
            angle = random.uniform(0, self.two_pi)
            speed = random.uniform(100, 300)
            direction = Vector2(math.cos(angle), math.sin(angle))
            pos = self.center + direction * self.radius
            vel = direction * speed
            lifetime = random.uniform(0.5, 1.5)
            self.particles.append(Particle(pos, vel, lifetime, self.color))
    
    def is_ball_in_gap(self, ball_angle: float) -> bool:
        normalized_ball = (ball_angle - self.rotation) % self.two_pi
        half_gap = self.gap_size / 2
        
        in_main_gap = normalized_ball <= half_gap + self.gap_tolerance or \
                     normalized_ball >= (self.two_pi - half_gap - self.gap_tolerance)
        
        return in_main_gap
    
    def update(self, dt: float, rotation_speed: float):
        if not self.destroyed:
            self.rotation += rotation_speed * dt
        
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, screen: pygame.Surface):
        if not self.destroyed or self.force_display:
            start_angle = self.rotation + self.gap_size / 2
            end_angle = self.rotation + self.two_pi - self.gap_size / 2
            
            for offset in range(self.thickness):
                radius = self.radius - offset
                rect = pygame.Rect(
                    self.center.x - radius,
                    self.center.y - radius,
                    radius * 2,
                    radius * 2
                )
                pygame.draw.arc(screen, self.color, rect, start_angle, end_angle, 1)
        
        for particle in self.particles:
            particle.draw(screen)
    
    def check_collision(self, ball_pos: Vector2, ball_radius: float) -> Tuple[bool, Vector2]:
        to_center = self.center - ball_pos
        distance = to_center.length()
        
        outer_radius = self.radius + CONFIG['spacing'] / 2
        inner_radius = self.radius - CONFIG['spacing'] / 2
        
        if inner_radius - ball_radius <= distance <= outer_radius + ball_radius:
            angle = math.atan2(to_center.y, to_center.x)
            if not self.is_ball_in_gap(angle):
                return True, to_center.normalize()
        return False, Vector2(0, 0)