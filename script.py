import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import colorsys
import time

# Configuration variables
CONFIG = {
    'width': 720,         # Window width
    'height': 1280,        # Window height
    'rings': 25,           # Number of rings
    'rotation': 1.5,       # Base rotation speed
    'ball_speed': 500,     # Initial ball speed
    'offset': 0.1,         # Rotation offset between rings
    'grow': True,          # Whether ball grows on collision
    'grow_size': 0.005,      # How much the ball grows on collision (pixels)
    'thickness': 2,        # Ring thickness
    'spacing': 15,         # Spacing between rings
    'gap_size': .75,      # Gap size in radians (0.25 = PI/4 = 45 degrees)
    'max_ring_radius': 0,  # Will be calculated based on window size
}

# Calculate maximum ring radius to fit window
CONFIG['max_ring_radius'] = min(CONFIG['width'], CONFIG['height']) * 0.45

@dataclass
class Vector2:
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self):
        length = self.length()
        if length == 0:
            return Vector2(0, 0)
        return Vector2(self.x / length, self.y / length)

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

class AudioManager:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        try:
            self.bounce = pygame.mixer.Sound('bounce.mp3')
            self.song = pygame.mixer.Sound('song.mp3')
        except:
            print("Warning: Could not load audio files")
            self.bounce = None
            self.song = None
        
        self.song_channel = pygame.mixer.Channel(0)
        self.bounce_channel = pygame.mixer.Channel(1)
        
        if self.song_channel and self.bounce_channel:
            self.song_channel.set_volume(0.7)
            self.bounce_channel.set_volume(0.7)
        
        self.current_second = 0
        self.last_collision_time = 0
        self.collision_cooldown = 0.1
        
        # Load the song into a numpy array for slicing
        if self.song:
            try:
                import pygame.sndarray
                self.song_array = pygame.sndarray.array(self.song)
                self.sample_rate = 44100  # Standard sample rate
                self.samples_per_second = self.sample_rate * 2  # Stereo, so *2
            except:
                print("Warning: Could not load song into array")
                self.song_array = None
    
    def play_song_snippet(self):
        if self.song and self.song_channel and self.song_array is not None:
            current_time = time.time()
            if current_time - self.last_collision_time > self.collision_cooldown:
                # Calculate start and end samples for the current second
                start_sample = self.current_second * self.samples_per_second
                end_sample = start_sample + self.samples_per_second
                
                if start_sample < len(self.song_array):
                    # Create a new sound from the slice
                    snippet = pygame.sndarray.make_sound(
                        self.song_array[start_sample:end_sample]
                    )
                    self.song_channel.play(snippet)
                    self.current_second += 1
                    self.last_collision_time = current_time
                else:
                    # Loop back to beginning if we've reached the end
                    self.current_second = 0
    
    def play_bounce(self):
        if self.bounce and self.bounce_channel:
            self.bounce_channel.play(self.bounce)

class Ball:
    def __init__(self, pos: Vector2, radius: float):
        self.pos = pos
        self.vel = Vector2(random.uniform(-1, 1), 
                          random.uniform(-1, 1)).normalize() * CONFIG['ball_speed']
        self.radius = radius
        self.base_radius = radius
        self.trail: List[Tuple[Vector2, float]] = []
        self.trail_length = 10
        self.restitution = 0.98  # Slight energy loss on collision
    
    def bounce(self, normal: Vector2):
        # Add slight randomization to the bounce
        random_angle = random.uniform(-0.2, 0.2)  # Small random angle adjustment
        cos_theta = math.cos(random_angle)
        sin_theta = math.sin(random_angle)
        
        # Rotate normal slightly
        rotated_normal = Vector2(
            normal.x * cos_theta - normal.y * sin_theta,
            normal.x * sin_theta + normal.y * cos_theta
        )
        
        # Calculate reflection
        dot_product = self.vel.x * rotated_normal.x + self.vel.y * rotated_normal.y
        self.vel = Vector2(
            self.vel.x - 2 * dot_product * rotated_normal.x,
            self.vel.y - 2 * dot_product * rotated_normal.y
        )
        
        # Apply restitution and ensure consistent speed
        speed = self.vel.length()
        self.vel = self.vel.normalize() * (speed * self.restitution)
        
        # Ensure minimum speed
        if self.vel.length() < CONFIG['ball_speed'] * 0.5:
            self.vel = self.vel.normalize() * CONFIG['ball_speed']
    
    def grow(self):
        if CONFIG['grow']:
            self.radius += CONFIG['grow_size']
    
    def update(self, dt: float):
        self.pos += self.vel * dt
        
        # Update trail
        self.trail.insert(0, (Vector2(self.pos.x, self.pos.y), 1.0))
        if len(self.trail) > self.trail_length:
            self.trail.pop()
        
        # Update trail fade
        for i in range(len(self.trail)):
            self.trail[i] = (self.trail[i][0], max(0, self.trail[i][1] - dt * 2))

    def draw(self, screen: pygame.Surface):
        # Draw trail
        for pos, alpha in self.trail:
            radius = self.radius * alpha
            color = (255, 255, 255, int(255 * alpha))
            surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            screen.blit(surf, (int(pos.x - radius), int(pos.y - radius)))
        
        # Draw ball
        pygame.draw.circle(screen, (255, 255, 255), 
                         (int(self.pos.x), int(self.pos.y)), 
                         int(self.radius))

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
        self.gap_tolerance = 0.1  # Tolerance for gap detection
    
    def create_destruction_particles(self):
        for _ in range(self.destruction_particles):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(100, 300)
            direction = Vector2(math.cos(angle), math.sin(angle))
            pos = self.center + direction * self.radius
            vel = direction * speed
            lifetime = random.uniform(0.5, 1.5)
            self.particles.append(Particle(pos, vel, lifetime, self.color))
    
    def is_ball_in_gap(self, ball_angle: float) -> bool:
        # Normalize angles to be between 0 and 2π
        normalized_ball = (ball_angle - self.rotation) % (2 * math.pi)
        half_gap = self.gap_size / 2
        
        # Check if ball is in the gap with tolerance
        in_main_gap = normalized_ball <= half_gap + self.gap_tolerance or \
                     normalized_ball >= (2 * math.pi - half_gap - self.gap_tolerance)
        
        return in_main_gap
    
    def update(self, dt: float, rotation_speed: float):
        if not self.destroyed:
            self.rotation += rotation_speed * dt
        
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
    
    def draw(self, screen: pygame.Surface):
        if not self.destroyed:
            start_angle = self.rotation + self.gap_size / 2
            end_angle = self.rotation + math.pi * 2 - self.gap_size / 2
            
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
        
        # Create a wider collision zone that extends halfway to adjacent rings
        outer_radius = self.radius + CONFIG['spacing'] / 2
        inner_radius = self.radius - CONFIG['spacing'] / 2
        
        if inner_radius - ball_radius <= distance <= outer_radius + ball_radius:
            angle = math.atan2(to_center.y, to_center.x)
            if not self.is_ball_in_gap(angle):
                return True, to_center.normalize()
        return False, Vector2(0, 0)

class Game:
    def __init__(self):
        pygame.init()
        self.width = CONFIG['width']
        self.height = CONFIG['height']
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.SRCALPHA)
        pygame.display.set_caption("Circle Escape")
        
        self.center = Vector2(self.width/2, self.height/2)
        self.ball = Ball(self.center, 8)
        self.rings: List[Ring] = []
        self.audio = AudioManager()
        self.active_ring_index = 0  # Track the innermost active ring
        self.setup_rings()
        
        self.clock = pygame.time.Clock()
        self.game_won = False
    
    def get_ring_color(self, index: int, total: int) -> Tuple[int, int, int]:
        hue = index / total
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
    
    def setup_rings(self):
        total_space = CONFIG['max_ring_radius'] - 50
        CONFIG['spacing'] = total_space / CONFIG['rings']
        
        base_radius = 50
        for i in range(CONFIG['rings']):
            radius = base_radius + i * CONFIG['spacing']
            color = self.get_ring_color(i, CONFIG['rings'])
            ring = Ring(self.center, radius, i * CONFIG['offset'], 
                       CONFIG['gap_size'], color)
            self.rings.append(ring)
        self.rings.sort(key=lambda r: r.radius)
    
    def get_innermost_active_ring(self) -> int:
        for i, ring in enumerate(self.rings):
            if not ring.destroyed:
                return i
        return len(self.rings)
    
    def check_ball_containment(self):
        if self.active_ring_index < len(self.rings):
            active_ring = self.rings[self.active_ring_index]
            to_center = active_ring.center - self.ball.pos
            distance = to_center.length()
            
            # If ball is outside the active ring's radius
            if distance > active_ring.radius + self.ball.radius:
                normal = to_center.normalize()
                self.ball.bounce(normal)
                self.audio.play_song_snippet()
                self.ball.grow()
                return True
        return False
    
    def check_gap_collision(self):
        if self.active_ring_index < len(self.rings):
            active_ring = self.rings[self.active_ring_index]
            to_center = active_ring.center - self.ball.pos
            distance = to_center.length()
            angle = math.atan2(-to_center.y, -to_center.x) + math.pi  # Corrected angle calculation
            
            # Widen the detection zone for gaps
            gap_detection_width = self.ball.radius + active_ring.thickness
            if abs(distance - active_ring.radius) < gap_detection_width:
                if active_ring.is_ball_in_gap(angle):
                    # Ball is in gap - destroy ring
                    active_ring.destroyed = True
                    active_ring.create_destruction_particles()
                    self.audio.play_bounce()
                    self.active_ring_index += 1  # Move to next ring
                    return True
                else:
                    # Bounce off ring
                    normal = to_center.normalize()
                    self.ball.bounce(normal)
                    self.audio.play_song_snippet()
                    self.ball.grow()
                    return True
        return False
    
    def check_collisions(self):
        self.active_ring_index = self.get_innermost_active_ring()
        
        # First check containment
        if self.check_ball_containment():
            return
        
        # Then check gap collisions
        self.check_gap_collision()
    
    def update_game_state(self, dt: float):
        if not self.game_won:
            self.ball.update(dt)
            
            # Update rings
            base_speed = CONFIG['rotation']
            for i, ring in enumerate(self.rings):
                ring.update(dt, base_speed * (1 + i * CONFIG['offset']))
            
            # Check collisions
            self.check_collisions()
            
            # Check win condition
            if all(ring.destroyed for ring in self.rings):
                self.game_won = True
    
    def draw(self):
        self.screen.fill((0, 0, 0))
        
        # Draw rings
        for ring in self.rings:
            ring.draw(self.screen)
        
        # Draw ball
        self.ball.draw(self.screen)
        
        # If game is won, draw victory message
        if self.game_won:
            font = pygame.font.Font(None, 74)
            text = font.render('Escaped!', True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width/2, self.height/2))
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True
    
    def run(self):
        running = True
        last_time = pygame.time.get_ticks()
        
        while running:
            # Handle timing
            current_time = pygame.time.get_ticks()
            dt = min((current_time - last_time) / 1000.0, 0.1)
            last_time = current_time
            
            # Process events
            running = self.handle_events()
            
            # Update game state
            self.update_game_state(dt)
            
            # Draw everything
            self.draw()
            
            # Maintain frame rate
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()