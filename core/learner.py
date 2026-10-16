import json
import os
from config import Config

class AdaptiveLearner:
    def __init__(self, profile_name="user_profile.json"):
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser('~')
        dir_path = os.path.join(app_data, 'HandController')
        os.makedirs(dir_path, exist_ok=True)
        
        self.profile_path = os.path.join(dir_path, profile_name)
        self.learning_rate = 0.02  # Smooth EMA to adapt over time
        
        # Initial estimates for normalized distances ('open' hand vs 'closed' pinch)
        self.profile = {
            'click': {'open': 1.2, 'closed': 0.2},
            'right_click': {'open': 1.2, 'closed': 0.2},
            'middle_click': {'open': 1.2, 'closed': 0.2},
            'scroll': {'open': 1.2, 'closed': 0.2},
            'minimize': {'open': 1.2, 'closed': 0.2}
        }
        self.load_profile()

    def load_profile(self):
        """Loads the learned patterns from disk if they exist."""
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, 'r') as f:
                    data = json.load(f)
                    for k in self.profile.keys():
                        if k in data:
                            self.profile[k] = data[k]
                self._apply_all_thresholds()
                print(f"Profile loaded from {self.profile_path}")
            except Exception as e:
                print(f"Error loading profile: {e}")
        else:
            self._apply_all_thresholds()

    def save_profile(self):
        """Saves the learned patterns to disk."""
        try:
            with open(self.profile_path, 'w') as f:
                json.dump(self.profile, f, indent=4)
            print(f"Profile saved to {self.profile_path}")
        except Exception as e:
            print(f"Error saving profile: {e}")

    def _apply_all_thresholds(self):
        """Applies all calculated thresholds to the global Config."""
        self._update_config('click', 'CLICK_IN_THRESHOLD', 'CLICK_OUT_THRESHOLD')
        self._update_config('right_click', 'RIGHT_CLICK_IN_THRESHOLD', 'RIGHT_CLICK_OUT_THRESHOLD')
        self._update_config('middle_click', 'MIDDLE_CLICK_IN_THRESHOLD', 'MIDDLE_CLICK_OUT_THRESHOLD')
        self._update_config('scroll', 'SCROLL_IN_THRESHOLD', 'SCROLL_OUT_THRESHOLD')
        self._update_config('minimize', 'MINIMIZE_IN_THRESHOLD', 'MINIMIZE_OUT_THRESHOLD')

    def _update_config(self, gesture, in_attr, out_attr):
        """Calculates IN and OUT thresholds based on open/closed clusters and sets them in Config."""
        open_val = self.profile[gesture]['open']
        closed_val = self.profile[gesture]['closed']
        
        span = open_val - closed_val
        if span > 0.1: # Ensure reasonable span
            # IN threshold is closer to the closed state (35% of the way to open)
            setattr(Config, in_attr, closed_val + 0.35 * span)
            # OUT threshold is closer to the open state (65% of the way to open)
            setattr(Config, out_attr, closed_val + 0.65 * span)

    def learn(self, gesture, distance):
        """Online Unsupervised Clustering step for a given gesture distance."""
        if gesture not in self.profile:
            return

        open_val = self.profile[gesture]['open']
        closed_val = self.profile[gesture]['closed']
        span = open_val - closed_val

        if span <= 0.05:
            # Prevent collapse of clusters
            self.profile[gesture]['open'] = closed_val + 0.1
            span = 0.1

        # If the distance is close to the 'closed' cluster, update the closed mean
        if distance < closed_val + 0.4 * span:
            self.profile[gesture]['closed'] = (1 - self.learning_rate) * closed_val + self.learning_rate * distance
        
        # If the distance is close to the 'open' cluster, update the open mean
        elif distance > closed_val + 0.6 * span:
            self.profile[gesture]['open'] = (1 - self.learning_rate) * open_val + self.learning_rate * distance

        # Sanity bounds to prevent extreme drift
        self.profile[gesture]['open'] = min(max(self.profile[gesture]['open'], 0.5), 3.0)
        self.profile[gesture]['closed'] = min(max(self.profile[gesture]['closed'], 0.01), 0.8)

        # Immediately update the Config so it feels responsive over time
        if gesture == 'click':
            self._update_config('click', 'CLICK_IN_THRESHOLD', 'CLICK_OUT_THRESHOLD')
        elif gesture == 'right_click':
            self._update_config('right_click', 'RIGHT_CLICK_IN_THRESHOLD', 'RIGHT_CLICK_OUT_THRESHOLD')
        elif gesture == 'middle_click':
            self._update_config('middle_click', 'MIDDLE_CLICK_IN_THRESHOLD', 'MIDDLE_CLICK_OUT_THRESHOLD')
        elif gesture == 'scroll':
            self._update_config('scroll', 'SCROLL_IN_THRESHOLD', 'SCROLL_OUT_THRESHOLD')
        elif gesture == 'minimize':
            self._update_config('minimize', 'MINIMIZE_IN_THRESHOLD', 'MINIMIZE_OUT_THRESHOLD')
