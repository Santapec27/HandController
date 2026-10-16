import time
import json
import os
from collections import deque
from cryptography.fernet import Fernet
from config import get_resource_path

class GestureLogger:
    def __init__(self, buffer_duration_sec=2.0):
        self.buffer_duration_sec = buffer_duration_sec
        self.buffer = deque()
        self.key_file = get_resource_path('.agprofile.key')
        self.log_file = get_resource_path('.agprofile_data')
        self.cipher = self._init_crypto()

    def _init_crypto(self):
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            with open(self.key_file, 'rb') as f:
                key = f.read()
        return Fernet(key)

    def log_frame(self, x, y, timestamp_ms, hand_state):
        """
        hand_state: e.g., 'hover', 'clicking', 'right_clicking'
        """
        # Append to buffer
        self.buffer.append({
            'x': x,
            'y': y,
            'timestamp': timestamp_ms,
            'state': hand_state
        })

        # Evict old frames (> buffer_duration_sec)
        current_time = timestamp_ms
        while len(self.buffer) > 0:
            oldest = self.buffer[0]
            if (current_time - oldest['timestamp']) > (self.buffer_duration_sec * 1000):
                self.buffer.popleft()
            else:
                break

    def save_success_trajectory(self):
        """
        Called when a click is successful. Saves the current buffer to the log file.
        """
        if len(self.buffer) < 5: # Too few points
            return
            
        trajectory = list(self.buffer)
        
        # We can analyze the trajectory here for friction/overshooting, 
        # but for now we just log the raw JSON
        
        entry = {
            'type': 'success_click_trajectory',
            'saved_at': int(time.time() * 1000),
            'points': trajectory
        }
        
        data_json = json.dumps(entry)
        encrypted_data = self.cipher.encrypt(data_json.encode('utf-8'))
        
        with open(self.log_file, 'ab') as f:
            f.write(encrypted_data + b'\n')

    def read_all_logs(self):
        """
        Reads and decrypts all logged trajectories.
        """
        if not os.path.exists(self.log_file):
            return []
            
        trajectories = []
        with open(self.log_file, 'rb') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    decrypted = self.cipher.decrypt(line).decode('utf-8')
                    trajectories.append(json.loads(decrypted))
                except Exception as e:
                    print(f"Failed to decrypt line: {e}")
                    
        return trajectories
