# Configuration variables
CONFIG = {
    'width': 720,         # Window width
    'height': 1280,       # Window height
    'rings': 25,          # Number of rings
    'rotation': 1.5,      # Base rotation speed
    'ball_speed': 750,    # Initial ball speed
    'offset': 0.1,        # Rotation offset between rings
    'grow': True,         # Whether ball grows on collision
    'grow_size': 0.005,   # How much the ball grows on collision (pixels)
    'thickness': 2,       # Ring thickness
    'spacing': 15,        # Spacing between rings
    'gap_size': .75,      # Gap size in radians (0.25 = PI/4 = 45 degrees)
    'max_ring_radius': 0, # Will be calculated based on window size
    'gravity': 0.0,       # Gravity affecting the ball (pixels/s²)
    'use_icon': True,     # Whether to use icon.png instead of circle
    'icon_size': 64,      # Size of the icon in pixels (both width and height)
    'bg_opacity': 0.5,    # Background video opacity (0.0 to 1.0)
    'tumble': True,       # Whether the ball/icon should spin when bouncing
    'tumble_velocity': 720.0,  # Degrees per second for tumbling
    'minimum_bounce_angle': 20.0,  # Minimum angle (in degrees) for bounces to prevent rolling
}

# Calculate maximum ring radius to fit window
CONFIG['max_ring_radius'] = min(CONFIG['width'], CONFIG['height']) * 0.45 