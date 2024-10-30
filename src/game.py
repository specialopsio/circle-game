import pygame
import colorsys
import math
from src.config import CONFIG
from src.utils.vector import Vector2
from src.entities.ball import Ball
from src.entities.ring import Ring
from src.managers.audio_manager import AudioManager
from typing import List, Tuple

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
            angle = math.atan2(-to_center.y, -to_center.x) + math.pi
            
            gap_detection_width = self.ball.radius + active_ring.thickness
            if abs(distance - active_ring.radius) < gap_detection_width:
                if active_ring.is_ball_in_gap(angle):
                    active_ring.destroyed = True
                    active_ring.create_destruction_particles()
                    self.audio.play_bounce()
                    self.active_ring_index += 1
                    return True
                else:
                    normal = to_center.normalize()
                    self.ball.bounce(normal)
                    self.audio.play_song_snippet()
                    self.ball.grow()
                    return True
        return False
    
    def check_collisions(self):
        self.active_ring_index = self.get_innermost_active_ring()
        
        if self.check_ball_containment():
            return
        
        self.check_gap_collision()
    
    def update_game_state(self, dt: float):
        if not self.game_won:
            self.ball.update(dt)
            
            base_speed = CONFIG['rotation']
            for i, ring in enumerate(self.rings):
                ring.update(dt, base_speed * (1 + i * CONFIG['offset']))
            
            self.check_collisions()
            
            if all(ring.destroyed for ring in self.rings):
                self.game_won = True
    
    def draw(self):
        self.screen.fill((0, 0, 0))
        
        for ring in self.rings:
            ring.draw(self.screen)
        
        self.ball.draw(self.screen)
        
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
            current_time = pygame.time.get_ticks()
            dt = min((current_time - last_time) / 1000.0, 0.1)
            last_time = current_time
            
            running = self.handle_events()
            self.update_game_state(dt)
            self.draw()
            
            self.clock.tick(60)
        
        pygame.quit()