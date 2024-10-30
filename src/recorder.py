import pygame
import os
from datetime import datetime
import subprocess

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
        self.temp_dir = os.path.join(self.output_dir, f"temp_{timestamp}")
        os.makedirs(self.temp_dir)
        
        self.final_filename = f"gameplay_{timestamp}.mp4"
        self.recording = True
        print(f"Started recording...")
    
    def capture_frame(self, screen: pygame.Surface):
        """Capture the current frame if recording is active"""
        if self.recording:
            # Save frame as PNG
            frame_filename = os.path.join(self.temp_dir, f"frame_{self.frame_count:06d}.png")
            pygame.image.save(screen, frame_filename)
            self.frame_count += 1
    
    def stop_recording(self):
        """Stop recording and combine frames into video"""
        if self.recording:
            try:
                print("Processing recording...")
                
                # Construct ffmpeg command for video creation
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file if it exists
                    '-framerate', '60',
                    '-i', os.path.join(self.temp_dir, 'frame_%06d.png'),
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '18',
                    '-pix_fmt', 'yuv420p',
                    os.path.join(self.output_dir, self.final_filename)
                ]
                
                # Execute ffmpeg command
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
                
                print(f"Recording saved to {os.path.join(self.output_dir, self.final_filename)}")
                print(f"Total frames recorded: {self.frame_count}")
                
                # Clean up temporary files
                for file in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, file))
                os.rmdir(self.temp_dir)
                
            except Exception as e:
                print(f"Warning: Error while processing recording: {str(e)}")
                print(f"Temporary files preserved in: {self.temp_dir}")
            
            self.recording = False