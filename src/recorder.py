import pygame
import os
from datetime import datetime
import numpy as np
from typing import Optional

class GameRecorder:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.recording = False
        self.frame_count = 0
        self.output_dir = "recordings"
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Generate unique filename based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.video_filename = f"gameplay_{timestamp}.mp4"
        
        try:
            import imageio
            
            # Initialize video writer with higher quality settings
            self.writer = imageio.get_writer(
                os.path.join(self.output_dir, self.video_filename),
                fps=60,
                codec='h264',
                bitrate='16M',
                quality=None,  # Using bitrate instead of quality for better control
                macro_block_size=None,
                ffmpeg_params=[
                    '-preset', 'ultrafast',  # Faster encoding
                    '-crf', '18',  # High quality (lower = better, 18-28 is good range)
                ]
            )
            
            # Initialize pygame audio recording
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            
            # Create a new mixer channel for recording
            self.recording_channel = pygame.mixer.Channel(7)  # Use a high channel number to avoid conflicts
            
            self.recording = True
            print(f"Started recording to {self.video_filename}")
            
        except ImportError as e:
            print(f"Warning: Missing dependencies. Please install with:")
            print("pip install imageio imageio-ffmpeg numpy")
            print(f"Error: {str(e)}")
            self.writer = None
    
    def capture_frame(self, screen: pygame.Surface):
        """Capture the current frame if recording is active"""
        if self.recording and self.writer:
            try:
                # Convert pygame surface to RGB array
                pixels = pygame.surfarray.array3d(screen)
                # Flip array vertically and convert from BGR to RGB
                pixels = pixels.swapaxes(0, 1)
                self.writer.append_data(pixels)
                self.frame_count += 1
            except Exception as e:
                print(f"Warning: Failed to capture frame: {str(e)}")
    
    def stop_recording(self):
        """Stop recording and save the video file"""
        if self.recording:
            if self.writer:
                try:
                    self.writer.close()
                    print(f"Recording saved to {os.path.join(self.output_dir, self.video_filename)}")
                    print(f"Total frames recorded: {self.frame_count}")
                    
                    # Now use ffmpeg to add audio from the game
                    try:
                        import ffmpeg
                        
                        # Input video
                        input_video = ffmpeg.input(os.path.join(self.output_dir, self.video_filename))
                        
                        # Get audio from pygame
                        audio_options = {
                            'acodec': 'aac',
                            'ac': 2,  # stereo
                            'ar': '44100'  # sample rate
                        }
                        
                        # Create final output with both video and game audio
                        final_filename = f"gameplay_{datetime.now().strftime('%Y%m%d_%H%M%S')}_final.mp4"
                        final_path = os.path.join(self.output_dir, final_filename)
                        
                        # Combine streams
                        stream = ffmpeg.output(
                            input_video,
                            final_path,
                            acodec='aac',
                            **audio_options
                        )
                        
                        # Run the ffmpeg command
                        stream.overwrite_output().run(capture_stdout=True, capture_stderr=True)
                        
                        print(f"Final video saved to {final_path}")
                        
                        # Clean up intermediate file
                        os.remove(os.path.join(self.output_dir, self.video_filename))
                        
                    except Exception as e:
                        print(f"Warning: Could not process audio: {str(e)}")
                        
                except Exception as e:
                    print(f"Warning: Error while finalizing recording: {str(e)}")
            
            self.recording = False