import time
import os
from typing import List

class AudioManager:
    def __init__(self):
        self.bounce = None
        self.song = None
        self.song_snippets: List = []
        self.song_channel = None
        self.bounce_channel = None
        self.bounce_count = 0
        self.current_snippet_index = 0
        
        # Initialize audio
        try:
            import pygame
            print("Attempting to load audio files...")
            self.bounce = pygame.mixer.Sound('bounce.mp3')
            self.song = pygame.mixer.Sound('song.mp3')
            print("Successfully loaded audio files")
            
            # Set up channels
            self.song_channel = pygame.mixer.Channel(0)
            self.bounce_channel = pygame.mixer.Channel(1)
            
            if self.song_channel and self.bounce_channel:
                self.song_channel.set_volume(0.7)
                self.bounce_channel.set_volume(0.7)
            
            # Split the song into one-second snippets
            try:
                print("Attempting to create song snippets...")
                import pygame.sndarray
                song_array = pygame.sndarray.array(self.song)
                sample_rate = 44100  # Hz
                num_channels = self.song.get_num_channels()
                samples_per_second = sample_rate * num_channels
                total_samples = song_array.shape[0]
                total_seconds = total_samples // samples_per_second
                print(f"Song length: {total_seconds} seconds")
                
                for i in range(total_seconds):
                    start = i * samples_per_second
                    end = start + samples_per_second
                    snippet_array = song_array[start:end]
                    snippet = pygame.sndarray.make_sound(snippet_array)
                    self.song_snippets.append(snippet)
                print(f"Successfully created {len(self.song_snippets)} snippets")
            except Exception as e:
                print(f"Warning: Could not create song snippets: {e}")
                # Fallback: just play the whole song
                self.song_snippets = [self.song]
        
        except Exception as e:
            print(f"Warning: Could not initialize audio: {e}")
            print("Current working directory:", os.path.abspath(os.curdir))
        
        self.last_collision_time = 0
        self.collision_cooldown = 0.1
    
    def play_song_snippet(self):
        if self.song_snippets and self.song_channel:
            current_time = time.time()
            if current_time - self.last_collision_time > self.collision_cooldown:
                # Play the next snippet in sequence
                print(f"Playing song snippet {self.current_snippet_index + 1}")
                self.song_channel.stop()
                self.song_snippets[self.current_snippet_index].play()
                
                # Increment and wrap around to start if we reach the end
                self.current_snippet_index = (self.current_snippet_index + 1) % len(self.song_snippets)
                self.last_collision_time = current_time
    
    def play_bounce(self):
        if self.bounce and self.bounce_channel:
            print("Playing bounce sound")
            self.bounce_channel.play(self.bounce)
    
    def reset_song_sequence(self):
        self.current_snippet_index = 0