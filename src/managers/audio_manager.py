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
        self.current_snippet_index = 0
        
        # Initialize audio with a higher quality
        try:
            import pygame
            pygame.mixer.init(
                frequency=44100,
                size=-16,
                channels=2,
                buffer=1024,
                allowedchanges=0
            )
            print("=== Audio Initialization ===")
            print("Attempting to load audio files...")
            self.bounce = pygame.mixer.Sound('bounce.mp3')
            self.song = pygame.mixer.Sound('song.mp3')
            print("Successfully loaded audio files")
            
            # Set up channels with higher quality
            self.song_channel = pygame.mixer.Channel(0)
            self.bounce_channel = pygame.mixer.Channel(1)
            
            if self.song_channel and self.bounce_channel:
                self.song_channel.set_volume(0.7)
                self.bounce_channel.set_volume(0.7)
            
            # Split the song into half-second snippets
            try:
                print("\n=== Snippet Creation ===")
                print("Step 1: Importing sndarray...")
                import pygame.sndarray
                
                print("Step 2: Converting sound to array...")
                song_array = pygame.sndarray.samples(self.song)
                print(f"Song array shape: {song_array.shape}")
                
                print("\nStep 3: Calculating dimensions...")
                sample_rate = pygame.mixer.get_init()[0]
                num_channels = 2
                samples_per_half_second = sample_rate // 2  # Changed to half second
                total_samples = song_array.shape[0]
                total_half_seconds = (total_samples // samples_per_half_second) * 2  # Multiply by 2 for half seconds
                
                print(f"Sample rate: {sample_rate}")
                print(f"Total samples: {total_samples}")
                print(f"Samples per half second: {samples_per_half_second}")
                print(f"Total half seconds: {total_half_seconds}")
                
                print("\nStep 4: Creating snippets...")
                for i in range(total_half_seconds):
                    start = i * samples_per_half_second
                    end = start + samples_per_half_second
                    if end > total_samples:
                        break
                    
                    snippet_array = song_array[start:end]
                    try:
                        snippet = pygame.sndarray.make_sound(snippet_array)
                        self.song_snippets.append(snippet)
                        print(f"Created snippet {i+1}")
                    except Exception as e:
                        print(f"Failed to create snippet {i+1}: {str(e)}")
                        raise e
                
                print(f"\nFinished! Created {len(self.song_snippets)} snippets")
                
            except Exception as e:
                print(f"\n!!! Snippet creation failed !!!")
                print(f"Error: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print("Traceback:")
                traceback.print_exc()
                self.song_snippets = [self.song]
                print("Falling back to using entire song as single snippet")
        
        except Exception as e:
            print(f"Warning: Could not initialize audio: {str(e)}")
            print("Current working directory:", os.path.abspath(os.curdir))
        
        self.last_collision_time = 0
        self.collision_cooldown = 0.1
        self.snippet_duration = 0.5  # Duration of each snippet in seconds
        self.current_snippet_start_time = 0
    
    def play_song_snippet(self):
        if self.song_snippets and self.song_channel:
            current_time = time.time()
            
            # Stop current snippet if it's been playing for half a second
            if current_time - self.current_snippet_start_time >= self.snippet_duration:
                self.song_channel.stop()
            
            if current_time - self.last_collision_time > self.collision_cooldown:
                self.song_channel.stop()
                self.song_snippets[self.current_snippet_index].play()
                
                # Update timing
                self.current_snippet_start_time = current_time
                self.last_collision_time = current_time
                
                # Increment and wrap around to start if we reach the end
                self.current_snippet_index = (self.current_snippet_index + 1) % len(self.song_snippets)
    
    def play_bounce(self):
        if self.bounce and self.bounce_channel:
            self.bounce_channel.play(self.bounce)
    
    def reset_song_sequence(self):
        self.current_snippet_index = 0