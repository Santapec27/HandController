import numpy as np
import time
from config import Config
from core.logger import GestureLogger
from core.ml_engine import MLEngine

class GestureProcessor:
    def __init__(self):
        self.logger = GestureLogger()
        self.ml_engine = MLEngine()
        self.reset()

    def reset(self):
        self.prev_x = None
        self.prev_y = None
        self.is_clicking = False
        self.is_right_clicking = False
        self.is_middle_clicking = False
        self.is_scrolling = False
        self.is_minimizing = False
        self.confidence = 1.0 # 1.0 (blue) to 0.0 (orange)

    def process(self, hand_landmarks):
        if not hand_landmarks:
            self.reset()
            return None, False, False, False, False, False, self.confidence

        # Get landmarks
        wrist = hand_landmarks[0]
        index_mcp = hand_landmarks[5]
        
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]
        ring_tip = hand_landmarks[16]
        pinky_tip = hand_landmarks[20]
        thumb_tip = hand_landmarks[4]

        # Calculate palm size for scale invariance
        palm_size = np.sqrt(
            (wrist.x - index_mcp.x)**2 + 
            (wrist.y - index_mcp.y)**2
        )
        # Avoid division by zero
        palm_size = max(palm_size, 0.001)

        # Calculate normalized distances
        thumb_index_dist = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2) / palm_size
        thumb_middle_dist = np.sqrt((middle_tip.x - thumb_tip.x)**2 + (middle_tip.y - thumb_tip.y)**2) / palm_size
        thumb_ring_dist = np.sqrt((ring_tip.x - thumb_tip.x)**2 + (ring_tip.y - thumb_tip.y)**2) / palm_size
        thumb_pinky_dist = np.sqrt((pinky_tip.x - thumb_tip.x)**2 + (pinky_tip.y - thumb_tip.y)**2) / palm_size
        
        max_all_fingers_dist = max([thumb_index_dist, thumb_middle_dist, thumb_ring_dist, thumb_pinky_dist])

        dists = [
            (thumb_index_dist, 'index'),
            (thumb_middle_dist, 'middle'),
            (thumb_ring_dist, 'ring'),
            (thumb_pinky_dist, 'pinky')
        ]
        dists.sort()
        min_dist, closest_finger = dists[0]

        hand_state = 'hover'

        # 1. Minimize Gesture
        if not self.is_minimizing:
            if max_all_fingers_dist < Config.MINIMIZE_IN_THRESHOLD:
                self.is_minimizing = True
                hand_state = 'minimizing'
                self.is_clicking = False
                self.is_right_clicking = False
                self.is_middle_clicking = False
                self.is_scrolling = False
        else:
            hand_state = 'minimizing'
            if max_all_fingers_dist > Config.MINIMIZE_OUT_THRESHOLD:
                self.is_minimizing = False
                hand_state = 'hover'

        # 2. Individual finger gestures
        if not self.is_minimizing:
            # Left click
            if not self.is_clicking:
                if closest_finger == 'index' and thumb_index_dist < Config.CLICK_IN_THRESHOLD:
                    self.is_clicking = True
                    # Just clicked successfully!
                    self.logger.save_success_trajectory()
            else:
                if thumb_index_dist > Config.CLICK_OUT_THRESHOLD:
                    self.is_clicking = False

            if self.is_clicking: hand_state = 'clicking'

            # Right click
            if not self.is_right_clicking:
                if closest_finger == 'middle' and thumb_middle_dist < Config.RIGHT_CLICK_IN_THRESHOLD:
                    self.is_right_clicking = True
            else:
                if thumb_middle_dist > Config.RIGHT_CLICK_OUT_THRESHOLD:
                    self.is_right_clicking = False
                    
            if self.is_right_clicking: hand_state = 'right_clicking'

            # Middle click
            if not self.is_middle_clicking:
                if closest_finger == 'ring' and thumb_ring_dist < Config.MIDDLE_CLICK_IN_THRESHOLD:
                    self.is_middle_clicking = True
            else:
                if thumb_ring_dist > Config.MIDDLE_CLICK_OUT_THRESHOLD:
                    self.is_middle_clicking = False
                    
            if self.is_middle_clicking: hand_state = 'middle_clicking'

            # Scroll
            if not self.is_scrolling:
                if closest_finger == 'pinky' and thumb_pinky_dist < Config.SCROLL_IN_THRESHOLD:
                    self.is_scrolling = True
            else:
                if thumb_pinky_dist > Config.SCROLL_OUT_THRESHOLD:
                    self.is_scrolling = False
                    
            if self.is_scrolling: hand_state = 'scrolling'

        # Map to screen coordinates using the index knuckle (MCP) instead of the fingertip.
        # This prevents the cursor from dropping down when the index finger bends to click!
        x, y = self.map_to_screen(index_mcp.x, index_mcp.y)
        timestamp_ms = int(time.time() * 1000)

        # Log frame
        self.logger.log_frame(x, y, timestamp_ms, hand_state)

        # Apply Magnetic Snap / Predictive ML
        x, y = self.ml_engine.apply_magnetic_snap(x, y, self.logger.buffer)

        # Smooth using Dynamic EMA
        if self.prev_x is None:
            self.prev_x, self.prev_y = x, y
        else:
            # Determine distance from previous frame
            dist_moved = np.sqrt((x - self.prev_x)**2 + (y - self.prev_y)**2)
            
            # If moving very fast, confidence drops slightly (orange)
            self.confidence = max(0.0, 1.0 - (dist_moved / 150.0))

            # Dynamic Alpha:
            # - When moving slowly (jitter), use strong smoothing (low alpha).
            # - When moving fast (intentional), use weak smoothing (high alpha) to avoid lag.
            if dist_moved < 5.0:
                # Deadzone for micro-jitters
                x, y = self.prev_x, self.prev_y
            else:
                # Scale alpha from 0.05 (extremely smooth) to 0.8 (responsive)
                # based on speed (distance moved per frame)
                speed_factor = np.clip((dist_moved - 5.0) / 60.0, 0.0, 1.0)
                dynamic_alpha = 0.05 + (speed_factor * 0.75)
                
                x = dynamic_alpha * x + (1 - dynamic_alpha) * self.prev_x
                y = dynamic_alpha * y + (1 - dynamic_alpha) * self.prev_y
                
            self.prev_x, self.prev_y = x, y

        return (int(x), int(y)), self.is_clicking, self.is_right_clicking, self.is_middle_clicking, self.is_scrolling, self.is_minimizing, self.confidence

    def map_to_screen(self, raw_x, raw_y):
        margin = Config.ROI_MARGIN_PERCENT
        
        # Clip to ROI
        constrained_x = np.clip(raw_x, margin, 1 - margin)
        constrained_y = np.clip(raw_y, margin, 1 - margin)

        # Normalize to 0-1 within ROI
        norm_x = (constrained_x - margin) / (1 - 2 * margin)
        norm_y = (constrained_y - margin) / (1 - 2 * margin)

        # Map to screen
        screen_x = norm_x * Config.SCREEN_WIDTH
        screen_y = norm_y * Config.SCREEN_HEIGHT
        
        return screen_x, screen_y
