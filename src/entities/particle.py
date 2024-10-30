import random
import pygame
from src.utils.vector import Vector2
from typing import Tuple

class Particle:
    def __init__(self, pos: Vector2, vel: Vector2, lifetime: float, color: Tuple[int, int, int]):
        self.pos = pos
        self.vel = vel
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.radius = random.uniform(1, 3)
    
    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        self.pos += self.vel * dt
        self.vel = self.vel * 0.98  # Add slight deceleration
        return self.lifetime > 0
    
    def draw(self, screen: pygame.Surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), 
                         (self.radius, self.radius), self.radius)
        screen.blit(surf, (int(self.pos.x - self.radius), 
                          int(self.pos.y - self.radius))) 