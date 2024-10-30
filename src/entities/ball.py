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
        self.trail_length = 5
        self.restitution = 0.98
        self.rotation = 0.0  # Current rotation in degrees
        self.angular_velocity = 0.0  # Current rotation speed in degrees/second
        
        # Try to load the icon if enabled
        self.icon = None
        if CONFIG['use_icon']:
            try:
                self.icon = pygame.image.load('icon.png').convert_alpha()
                # Scale the icon to the configured size
                icon_size = CONFIG['icon_size']
                self.icon = pygame.transform.smoothscale(self.icon, (icon_size, icon_size))
                # Adjust the radius to match half the icon size
                self.radius = icon_size / 2
                self.base_radius = self.radius
            except:
                print("Warning: Could not load icon.png, falling back to circle")
                CONFIG['use_icon'] = False
    
    def bounce(self, normal: Vector2):
        # Get the current velocity angle
        current_angle = math.degrees(math.atan2(self.vel.y, self.vel.x))
        
        # Calculate the angle between the velocity and the normal
        dot_product = self.vel.x * normal.x + self.vel.y * normal.y
        bounce_angle = math.degrees(math.acos(max(-1.0, min(1.0, dot_product / self.vel.length()))))
        
        # If the bounce angle is too shallow, adjust it
        if bounce_angle < CONFIG['minimum_bounce_angle']:
            # Calculate new bounce direction
            perpendicular = Vector2(-normal.y, normal.x)
            sign = 1 if self.vel.x * perpendicular.x + self.vel.y * perpendicular.y > 0 else -1
            min_angle_rad = math.radians(CONFIG['minimum_bounce_angle'])
            new_dir = Vector2(
                normal.x * math.cos(min_angle_rad) + sign * perpendicular.x * math.sin(min_angle_rad),
                normal.y * math.cos(min_angle_rad) + sign * perpendicular.y * math.sin(min_angle_rad)
            )
            self.vel = new_dir.normalize() * self.vel.length()
        else:
            # Regular bounce calculation
            dot_product = self.vel.x * normal.x + self.vel.y * normal.y
            self.vel = Vector2(
                self.vel.x - 2 * dot_product * normal.x,
                self.vel.y - 2 * dot_product * normal.y
            )
        
        # Apply restitution
        speed = self.vel.length()
        self.vel = self.vel.normalize() * (speed * self.restitution)
        
        # Ensure minimum speed
        if self.vel.length() < CONFIG['ball_speed'] * 0.5:
            self.vel = self.vel.normalize() * CONFIG['ball_speed']
        
        # Apply tumble if enabled
        if CONFIG['tumble']:
            # Calculate tumble direction based on bounce angle
            tumble_direction = 1 if bounce_angle > 90 else -1
            self.angular_velocity = CONFIG['tumble_velocity'] * tumble_direction
    
    def grow(self):
        if CONFIG['grow']:
            self.radius += CONFIG['grow_size']
    
    def update(self, dt: float):
        if CONFIG['gravity'] != 0.0:
            self.vel.y += CONFIG['gravity'] * dt
        
        self.pos += self.vel * dt
        
        # Update rotation
        self.rotation += self.angular_velocity * dt
        # Keep rotation between 0 and 360 degrees
        self.rotation = self.rotation % 360
        
        # Gradually reduce angular velocity
        self.angular_velocity *= 0.99
        
        self.trail.insert(0, (Vector2(self.pos.x, self.pos.y), 0.4))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        for i in range(len(self.trail)):
            self.trail[i] = (self.trail[i][0], max(0, self.trail[i][1] - dt * 2))
    
    def draw(self, screen: pygame.Surface):
        for pos, alpha in self.trail:
            if not CONFIG['use_icon'] or not self.icon:
                # Draw regular circle trail
                radius = self.radius * alpha
                color = (255, 255, 255, int(255 * alpha))
                surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (radius, radius), radius)
                screen.blit(surf, (int(pos.x - radius), int(pos.y - radius)))
            else:
                # Draw icon trail with transparency
                scaled_icon = self.icon.copy()
                scaled_icon.set_alpha(int(255 * alpha))
                icon_rect = scaled_icon.get_rect(center=(pos.x, pos.y))
                screen.blit(scaled_icon, icon_rect)
        
        if not CONFIG['use_icon'] or not self.icon:
            # Draw regular circle ball
            pygame.draw.circle(screen, (255, 255, 255), 
                             (int(self.pos.x), int(self.pos.y)), 
                             int(self.radius))
        else:
            # Draw rotated icon ball
            rotated_icon = pygame.transform.rotate(self.icon, self.rotation)
            icon_rect = rotated_icon.get_rect(center=(self.pos.x, self.pos.y))
            screen.blit(rotated_icon, icon_rect)