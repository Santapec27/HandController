import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from config import get_resource_path

class HandDetector:
    def __init__(self):
        base_options = python.BaseOptions(model_asset_path=get_resource_path('assets/hand_landmarker.task'))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, frame, timestamp_ms):
        # Flip the frame horizontally for natural mirror feel
        frame = cv2.flip(frame, 1)
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.detector.detect_for_video(mp_image, timestamp_ms)
        return results
