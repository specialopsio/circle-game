# Configuration variables
CONFIG = {
    'width': 720,         # Window width
    'height': 1280,       # Window height
    'rings': 25,          # Number of rings
    'rotation': 1.5,      # Base rotation speed
    'ball_speed': 500,    # Initial ball speed
    'offset': 0.1,        # Rotation offset between rings
    'grow': True,         # Whether ball grows on collision
    'grow_size': 0.005,   # How much the ball grows on collision (pixels)
    'thickness': 2,       # Ring thickness
    'spacing': 15,        # Spacing between rings
    'gap_size': .75,      # Gap size in radians (0.25 = PI/4 = 45 degrees)
    'max_ring_radius': 0, # Will be calculated based on window size
    'gravity': 0.0,       # Gravity affecting the ball (pixels/s²)
}

# Calculate maximum ring radius to fit window
CONFIG['max_ring_radius'] = min(CONFIG['width'], CONFIG['height']) * 0.45 