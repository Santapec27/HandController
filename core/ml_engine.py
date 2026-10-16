import os
import json
import numpy as np
from sklearn.linear_model import Ridge
from config import Config, get_resource_path
from core.logger import GestureLogger

class MLEngine:
    def __init__(self):
        self.logger = GestureLogger()
        self.profile_file = get_resource_path('.agprofile')
        self.velocity_model = Ridge(alpha=1.0)
        self.is_trained = False
        
        # Load local profile if it exists
        self.profile = self._load_profile()
        self._apply_profile()

    def _load_profile(self):
        if os.path.exists(self.profile_file):
            try:
                with open(self.profile_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'avg_velocity': 0.0,
            'optimized_gestures_count': 0,
            'ema_alpha': Config.EMA_ALPHA
        }

    def _save_profile(self):
        with open(self.profile_file, 'w') as f:
            json.dump(self.profile, f)

    def _apply_profile(self):
        Config.EMA_ALPHA = self.profile.get('ema_alpha', Config.EMA_ALPHA)

    def train_on_logs(self):
        """
        Processes saved trajectories to adjust EMA_ALPHA.
        Called on exit or periodically.
        """
        trajectories = self.logger.read_all_logs()
        if not trajectories:
            return

        velocities = []
        for traj in trajectories:
            pts = traj.get('points', [])
            if len(pts) < 2:
                continue
            
            # Calculate average velocity in this trajectory
            dx = pts[-1]['x'] - pts[0]['x']
            dy = pts[-1]['y'] - pts[0]['y']
            dt = (pts[-1]['timestamp'] - pts[0]['timestamp']) / 1000.0 # seconds
            if dt > 0:
                v = np.sqrt(dx**2 + dy**2) / dt
                velocities.append(v)
        
        if velocities:
            avg_v = np.mean(velocities)
            self.profile['avg_velocity'] = float(avg_v)
            
            # Simple heuristic: higher velocity -> more smoothing (lower alpha)
            # lower velocity -> less smoothing (higher alpha) to avoid lag
            # Base EMA_ALPHA is 0.5. Range [0.2, 0.8]
            # Assuming max normal velocity is around 2000 px/sec
            normalized_v = min(avg_v / 2000.0, 1.0)
            new_alpha = 0.8 - (normalized_v * 0.6) 
            self.profile['ema_alpha'] = max(0.2, min(0.8, new_alpha))
            
            self._save_profile()
            self._apply_profile()

    def increment_optimized_gestures(self):
        self.profile['optimized_gestures_count'] += 1
        self._save_profile()

    def apply_magnetic_snap(self, current_x, current_y, buffer):
        """
        Predicts intention based on the last few frames.
        If the user is moving slowly towards a likely target, snap to it.
        For simplicity, we'll just add a slight velocity-based prediction (extrapolation).
        """
        if len(buffer) < 3:
            return current_x, current_y
            
        p1 = buffer[-3]
        p2 = buffer[-1]
        
        dt = (p2['timestamp'] - p1['timestamp']) / 1000.0
        if dt <= 0 or dt > 0.5:
            return current_x, current_y
            
        vx = (p2['x'] - p1['x']) / dt
        vy = (p2['y'] - p1['y']) / dt
        
        # If moving very slowly, might be overshooting/trembling. We dampen it.
        speed = np.sqrt(vx**2 + vy**2)
        
        # Smoothly scale predictive extrapolation based on speed.
        # Below 50 px/s: 0 prediction (stable).
        # Above 300 px/s: 0.05s prediction.
        # In between: smooth interpolation.
        if speed < 50:
            pred_factor = 0.0
            self.increment_optimized_gestures()
        else:
            pred_factor = np.clip((speed - 50) / 250.0, 0.0, 1.0) * 0.05
            
        pred_x = current_x + vx * pred_factor
        pred_y = current_y + vy * pred_factor
        
        return pred_x, pred_y
