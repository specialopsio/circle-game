import pygame
import colorsys
import math
import os
import cv2
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
        self.game_started = False
        self.two_pi = math.pi * 2
        
        # Video background setup
        self.bg_video = None
        self.bg_surface = None
        if os.path.exists('bg.mp4'):
            self.setup_video_background()
            # Capture first frame but don't start playing
            self.update_video_background(force_first_frame=True)
    
    def setup_video_background(self):
        """Initialize video background if bg.mp4 exists"""
        try:
            self.bg_video = cv2.VideoCapture('bg.mp4')
            if not self.bg_video.isOpened():
                print("Warning: Could not open bg.mp4")
                return
            
            # Create a pygame surface for the video frame
            self.bg_surface = pygame.Surface((self.width, self.height))
            print("Successfully loaded background video")
        except Exception as e:
            print(f"Warning: Error setting up video background: {str(e)}")
            self.bg_video = None
    
    def update_video_background(self, force_first_frame=False):
        """Update the video frame"""
        if self.bg_video is None or self.bg_surface is None:
            return
        
        # Only update video if game has started or we're forcing first frame
        if not (self.game_started or force_first_frame):
            return
        
        ret, frame = self.bg_video.read()
        if not ret:
            # Video ended, loop back to start
            self.bg_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.bg_video.read()
        
        if ret:
            # Calculate scaling to match height while maintaining aspect ratio
            video_height = frame.shape[0]
            video_width = frame.shape[1]
            scale_factor = self.height / video_height
            new_width = int(video_width * scale_factor)
            
            # Resize frame
            frame = cv2.resize(frame, (new_width, self.height))
            
            # Center the frame horizontally
            x_offset = max(0, (new_width - self.width) // 2)
            frame = frame[:, x_offset:x_offset + self.width] if new_width > self.width else frame
            
            # Create a surface for the frame
            video_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            
            # Convert frame to pygame surface
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
            
            # Create a surface for the alpha channel
            alpha_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha_surface.fill((255, 255, 255, int(255 * CONFIG['bg_opacity'])))
            
            # Blit the frame and apply alpha
            video_surface.blit(frame_surface, (0, 0))
            video_surface.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            self.bg_surface = video_surface
    
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
    
    def start_game(self):
        """Initialize game state when space is pressed"""
        self.game_started = True
        # Give the ball an initial bounce
        self.ball.vel = Vector2(0, -1).normalize() * CONFIG['ball_speed']
        self.audio.reset_song_sequence()
        # Reset video to start
        if self.bg_video is not None:
            self.bg_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
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
            #to_center.y *= -1.0

            from_center = self.ball.pos - active_ring.center
            from_center.y *= -1.0

            distance = to_center.length()
            angle = (math.atan2(from_center.y, from_center.x) + self.two_pi) % self.two_pi
            
            gap_detection_width = self.ball.radius + active_ring.thickness

            if abs(active_ring.radius - distance) < gap_detection_width:
                #print(f"ball: {from_center},  radius: {distance}, angle: {angle * 360/self.two_pi}, active ring: {self.active_ring_index}, radius: {active_ring.radius}, gap: {(active_ring.rotation % self.two_pi) * 360/self.two_pi}")  
                if active_ring.is_ball_in_gap(angle):
                    active_ring.destroyed = True
                    #print(f"ring {self.active_ring_index}/{len(self.rings)} with radius {active_ring.radius} is destroyed")
                    self.active_ring_index += 1
                    #if self.active_ring_index == len(self.rings):
                    #    active_ring.force_display = True
                    active_ring.create_destruction_particles()
                    self.audio.play_bounce()
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
        if not self.game_started:
            return
            
        if not self.game_won:
            self.ball.update(dt, None if self.active_ring_index >= len(self.rings) else self.rings[self.active_ring_index])
            
            base_speed = CONFIG['rotation']
            for i, ring in enumerate(self.rings):
                ring.update(dt, base_speed * (1 + i * CONFIG['offset']))
            
            self.check_collisions()
            
            if all(ring.destroyed for ring in self.rings):
                self.game_won = True
    
    def draw(self):
        # Start with a black background
        self.screen.fill((0, 0, 0))
        
        # Draw video background if available
        if self.bg_surface is not None:
            self.screen.blit(self.bg_surface, (0, 0))
        
        # Draw game elements on top
        for ring in self.rings:
            ring.draw(self.screen)
        
        self.ball.draw(self.screen)
        
        if not self.game_started:
            font = pygame.font.Font(None, 74)
            text = font.render('Press SPACE to Start', True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width/2, self.height/2))
            self.screen.blit(text, text_rect)
        elif self.game_won:
            font = pygame.font.Font(None, 74)
            text = font.render('Escaped!', True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.width/2, self.height/2))
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_started:
                    self.start_game()
        return True
    
    def run(self):
        running = True
        last_time = pygame.time.get_ticks()
        
        # Target 60 FPS
        target_fps = 60
        target_frame_time = 1000 / target_fps  # in milliseconds
        
        while running:
            frame_start = pygame.time.get_ticks()
            
            current_time = pygame.time.get_ticks()
            dt = min((current_time - last_time) / 1000.0, 0.1)
            last_time = current_time
            
            running = self.handle_events()
            self.update_game_state(dt)
            
            # Update video background
            self.update_video_background()
            
            self.draw()
            
            # Calculate how long to wait
            frame_time = pygame.time.get_ticks() - frame_start
            if frame_time < target_frame_time:
                pygame.time.wait(int(target_frame_time - frame_time))
            
            # Update display at exactly 60fps
            self.clock.tick(target_fps)
        
        # Clean up video capture
        if self.bg_video is not None:
            self.bg_video.release()
        
        pygame.quit()