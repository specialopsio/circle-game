from src.utils.vector import Vector2
from src.config import CONFIG
import pygame
import random
import math
from typing import List, Tuple
from src.entities.ring import Ring

class Ball:
    def __init__(self, pos: Vector2, radius: float):
        self.pos = pos
        self.vel = Vector2(random.uniform(-1, 1), 
                          random.uniform(-1, 1)).normalize() * CONFIG['ball_speed']
        self.radius = radius
        self.base_radius = radius
        self.trail: List[Tuple[Vector2, float, float]] = []
        self.trail_length = 5
        self.restitution = 0.98
        self.rotation = 0.0
        self.angular_velocity = 0.0
        self.last_bounce_pos = None
        self.consecutive_bounces = 0
        self.last_bounce_time = 0
        
        # Try to load the icon if enabled
        self.icon = None
        if CONFIG['use_icon']:
            try:
                self.icon = pygame.image.load('icon.png').convert_alpha()
                icon_size = CONFIG['icon_size']
                self.icon = pygame.transform.smoothscale(self.icon, (icon_size, icon_size))
                self.radius = icon_size / 2
                self.base_radius = self.radius
            except:
                print("Warning: Could not load icon.png, falling back to circle")
                CONFIG['use_icon'] = False
    
    def is_edge_rolling(self, normal: Vector2) -> bool:
        """Detect if the ball is rolling along an edge"""
        current_time = pygame.time.get_ticks() / 1000.0
        
        # Check if this bounce is very close to the last bounce
        if self.last_bounce_pos is not None:
            distance_to_last = (self.pos - self.last_bounce_pos).length()
            time_since_last = current_time - self.last_bounce_time
            
            if distance_to_last < self.radius * 4 and time_since_last < 0.1:
                self.consecutive_bounces += 1
            else:
                self.consecutive_bounces = 0
        
        self.last_bounce_pos = Vector2(self.pos.x, self.pos.y)
        self.last_bounce_time = current_time
        
        return self.consecutive_bounces >= 2
    
    def get_escape_vector(self, normal: Vector2) -> Vector2:
        """Calculate a vector to escape edge rolling"""
        # Get perpendicular direction to the normal
        perpendicular = Vector2(-normal.y, normal.x)
        
        # Add a strong outward component and some randomness
        escape_angle = math.radians(random.uniform(30, 60))
        escape_dir = Vector2(
            normal.x * math.cos(escape_angle) + perpendicular.x * math.sin(escape_angle),
            normal.y * math.cos(escape_angle) + perpendicular.y * math.sin(escape_angle)
        )
        
        return escape_dir.normalize()
    
    def bounce(self, normal: Vector2):
        if self.is_edge_rolling(normal):
            # If we detect edge rolling, use escape vector
            escape_dir = self.get_escape_vector(normal)
            self.vel = escape_dir * (CONFIG['ball_speed'] * 1.2)  # Slightly faster to ensure escape
            self.consecutive_bounces = 0
        else:
            # Regular bounce logic with improved angle handling
            dot_product = self.vel.x * normal.x + self.vel.y * normal.y
            bounce_angle = math.degrees(math.acos(max(-1.0, min(1.0, dot_product / self.vel.length()))))
                        
            if bounce_angle < CONFIG['minimum_bounce_angle']:
                # More aggressive angle adjustment for shallow bounces
                perpendicular = Vector2(-normal.y, normal.x)
                sign = 1 if self.vel.x * perpendicular.x + self.vel.y * perpendicular.y > 0 else -1
                min_angle_rad = math.radians(CONFIG['minimum_bounce_angle'] + random.uniform(10, 25))
                
                new_dir = Vector2(
                    normal.x * math.cos(min_angle_rad) + sign * perpendicular.x * math.sin(min_angle_rad),
                    normal.y * math.cos(min_angle_rad) + sign * perpendicular.y * math.sin(min_angle_rad)
                )
                self.vel = new_dir.normalize() * (CONFIG['ball_speed'] * random.uniform(1.0, 1.2))
            else:
                # Add more randomness for shallow angles
                random_angle = (random.uniform(-15, 15) if bounce_angle < 45 or bounce_angle > 135 else random.uniform(-5, 5))

                # Regular bounce with added randomness
                rot_angle = math.radians(random_angle)
                cos_theta = math.cos(rot_angle)
                sin_theta = math.sin(rot_angle)

                #print("bounce angle + rnd", random_angle+bounce_angle)
                
                rotated_normal = Vector2(
                    normal.x * cos_theta - normal.y * sin_theta,
                    normal.x * sin_theta + normal.y * cos_theta
                )
                
                #dot_product = self.vel.x * rotated_normal.x + self.vel.y * rotated_normal.y
                #self.vel = Vector2(
                #    self.vel.x - 2 * dot_product * rotated_normal.x,
                #    self.vel.y - 2 * dot_product * rotated_normal.y
                #)

                speed = self.vel.length() * random.uniform(0.95, 1.05)
                self.vel = rotated_normal 
                
                # Ensure minimum velocity and add some randomness
                self.vel = self.vel.normalize() * max(speed, CONFIG['ball_speed'] * 0.8)
        
        # Apply tumble if enabled
        if CONFIG['tumble']:
            tumble_direction = random.choice([-1, 1])  # Randomize tumble direction
            random_multiplier = random.uniform(0.8, 1.2)
            self.angular_velocity = CONFIG['tumble_velocity'] * tumble_direction * random_multiplier
    
    def grow(self):
        if CONFIG['grow']:
            self.radius += CONFIG['grow_size']
    
    def update(self, dt: float, active_ring: Ring = None):
        if CONFIG['gravity'] != 0.0:
            self.vel.y += CONFIG['gravity'] * dt
        
        #if active_ring != None:
        #    print(self.pos, self.pos - active_ring.center, self.vel, dt)
        #else:
        #    print(self.pos, self.pos, self.vel, dt)

        self.pos += self.vel * dt
             
        if active_ring != None:
            # check pos w.r.t. active ring
            ball_to_center = self.pos - active_ring.center
            ball_distance = ball_to_center.length()
            if ball_distance > active_ring.radius:
                # correct position
                angle = math.atan2(ball_to_center.y, ball_to_center.x)
                self.pos.x = math.cos(angle) * ball_distance + active_ring.center.x
                self.pos.y = math.sin(angle) * ball_distance + active_ring.center.y
                print(f"Fixing position")

        # Update rotation
        self.rotation += self.angular_velocity * dt
        # Keep rotation between 0 and 360 degrees
        self.rotation = self.rotation % 360
        
        # Gradually reduce angular velocity
        self.angular_velocity *= 0.99
        
        # Add current position and rotation to trail
        self.trail.insert(0, (Vector2(self.pos.x, self.pos.y), 0.4, self.rotation))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        for i in range(len(self.trail)):
            pos, alpha, rot = self.trail[i]
            self.trail[i] = (pos, max(0, alpha - dt * 2), rot)
    
    def draw(self, screen: pygame.Surface):
        for pos, alpha, rotation in self.trail:
            if not CONFIG['use_icon'] or not self.icon:
                # Draw regular circle trail
                radius = self.radius * alpha
                color = (255, 255, 255, int(255 * alpha))
                surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (radius, radius), radius)
                screen.blit(surf, (int(pos.x - radius), int(pos.y - radius)))
            else:
                # Draw rotating icon trail with transparency
                scaled_icon = self.icon.copy()
                scaled_icon.set_alpha(int(255 * alpha))
                # Rotate the trail icon
                rotated_icon = pygame.transform.rotate(scaled_icon, rotation)
                icon_rect = rotated_icon.get_rect(center=(pos.x, pos.y))
                screen.blit(rotated_icon, icon_rect)
        
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