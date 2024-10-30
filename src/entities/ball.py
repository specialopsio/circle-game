from src.utils.vector import Vector2
from src.config import CONFIG
import pygame
import random
import math
from typing import List, Tuple

class Ball:
    def __init__(self, pos: Vector2, radius: float):
        self.pos = pos
        self.vel = Vector2(random.uniform(-1, 1), 
                          random.uniform(-1, 1)).normalize() * CONFIG['ball_speed']
        self.radius = radius
        self.base_radius = radius
        self.trail: List[Tuple[Vector2, float]] = []
        self.trail_length = 10
        self.restitution = 0.98
    
    def bounce(self, normal: Vector2):
        random_angle = random.uniform(-0.2, 0.2)
        cos_theta = math.cos(random_angle)
        sin_theta = math.sin(random_angle)
        
        rotated_normal = Vector2(
            normal.x * cos_theta - normal.y * sin_theta,
            normal.x * sin_theta + normal.y * cos_theta
        )
        
        dot_product = self.vel.x * rotated_normal.x + self.vel.y * rotated_normal.y
        self.vel = Vector2(
            self.vel.x - 2 * dot_product * rotated_normal.x,
            self.vel.y - 2 * dot_product * rotated_normal.y
        )
        
        speed = self.vel.length()
        self.vel = self.vel.normalize() * (speed * self.restitution)
        
        if self.vel.length() < CONFIG['ball_speed'] * 0.5:
            self.vel = self.vel.normalize() * CONFIG['ball_speed']
    
    def grow(self):
        if CONFIG['grow']:
            self.radius += CONFIG['grow_size']
    
    def update(self, dt: float):
        if CONFIG['gravity'] != 0.0:
            self.vel.y += CONFIG['gravity'] * dt
        
        self.pos += self.vel * dt
        
        self.trail.insert(0, (Vector2(self.pos.x, self.pos.y), 1.0))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        for i in range(len(self.trail)):
            self.trail[i] = (self.trail[i][0], max(0, self.trail[i][1] - dt * 2))
    
    def draw(self, screen: pygame.Surface):
        for pos, alpha in self.trail:
            radius = self.radius * alpha
            color = (255, 255, 255, int(255 * alpha))
            surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            screen.blit(surf, (int(pos.x - radius), int(pos.y - radius)))
        
        pygame.draw.circle(screen, (255, 255, 255), 
                         (int(self.pos.x), int(self.pos.y)), 
                         int(self.radius))