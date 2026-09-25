"""
hand_tracker.py

Detects and tracks a single hand using MediaPipe Hands.

The tracker provides the detected landmarks, optional landmark drawing,
and the positions of the palm and index fingertip used by the gesture
controller and board mapper.
"""

import cv2
import mediapipe as mp


class HandTracker:
    """Detect and track one hand with MediaPipe."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

    def process(self, frame):
        """
        Detect a hand in the given frame.

        Returns:
            MediaPipe hand landmarks, or None when no hand is detected.
        """
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return None

        return result.multi_hand_landmarks[0]

    def draw(self, frame, landmarks):
        """Draw detected hand landmarks and connections on a frame."""
        if landmarks is not None:
            self.mp_draw.draw_landmarks(
                frame,
                landmarks,
                self.mp_hands.HAND_CONNECTIONS
            )

    def get_palm_position(self, landmarks):
        """
        Return the normalized palm position.

        MediaPipe landmark 9 is used as the palm reference point.
        """
        if landmarks is None:
            return None

        x = landmarks.landmark[9].x
        y = landmarks.landmark[9].y

        return x, y

    def get_finger_position(self, landmarks):
        """
        Return the normalized index fingertip position.

        MediaPipe landmark 8 is used as the index fingertip.
        """
        if landmarks is None:
            return None

        x = landmarks.landmark[8].x
        y = landmarks.landmark[8].y

        return x, y

    def close(self):
        """Release MediaPipe hand-tracking resources."""
        self.hands.close()