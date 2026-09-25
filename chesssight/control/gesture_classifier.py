"""
gesture_classifier.py

Classifies hand gestures from MediaPipe hand landmarks.

Supported gestures:
- FIST
- TWO_FINGERS
- OPEN_PALM
- UNKNOWN

GestureStabilizer reduces short recognition flickering by requiring
the same gesture to be detected across several frames.
"""

import math
from collections import Counter, deque


def angle(a, b, c):
    """Return the angle ABC in degrees."""
    ab = (
        a.x - b.x,
        a.y - b.y,
        a.z - b.z
    )

    cb = (
        c.x - b.x,
        c.y - b.y,
        c.z - b.z
    )

    dot = (
        ab[0] * cb[0]
        + ab[1] * cb[1]
        + ab[2] * cb[2]
    )

    len_ab = math.sqrt(
        ab[0] ** 2
        + ab[1] ** 2
        + ab[2] ** 2
    )

    len_cb = math.sqrt(
        cb[0] ** 2
        + cb[1] ** 2
        + cb[2] ** 2
    )

    if len_ab == 0 or len_cb == 0:
        return 0

    cos_value = dot / (len_ab * len_cb)
    cos_value = max(-1.0, min(1.0, cos_value))

    return math.degrees(math.acos(cos_value))


def finger_extended(landmarks, mcp, pip, dip, tip):
    """
    Check whether a finger is extended.

    The function uses the angles between the finger joints.
    """
    angle_1 = angle(
        landmarks[mcp],
        landmarks[pip],
        landmarks[dip]
    )

    angle_2 = angle(
        landmarks[pip],
        landmarks[dip],
        landmarks[tip]
    )

    return angle_1 > 150 and angle_2 > 150


def classify_gesture(landmarks):
    """
    Classify a MediaPipe hand landmark result.

    Returns:
        FIST
        TWO_FINGERS
        OPEN_PALM
        UNKNOWN
    """
    points = landmarks.landmark

    index = finger_extended(points, 5, 6, 7, 8)
    middle = finger_extended(points, 9, 10, 11, 12)
    ring = finger_extended(points, 13, 14, 15, 16)
    pinky = finger_extended(points, 17, 18, 19, 20)

    fingers = [index, middle, ring, pinky]

    if not any(fingers):
        return "FIST"

    if index and middle and not ring and not pinky:
        return "TWO_FINGERS"

    if all(fingers):
        return "OPEN_PALM"

    return "UNKNOWN"


class GestureStabilizer:
    """
    Stabilize gesture recognition over multiple frames.

    A gesture becomes stable only when it appears at least
    `required` times within the history window.
    """

    def __init__(self, size=5, required=3):
        self.history = deque(maxlen=size)
        self.required = required

    def update(self, gesture):
        """Add a gesture sample and return the current stable gesture."""
        self.history.append(gesture)

        if not self.history:
            return "UNKNOWN"

        counts = Counter(self.history)
        stable_gesture, count = counts.most_common(1)[0]

        if count >= self.required:
            return stable_gesture

        return "UNKNOWN"

    def reset(self):
        """Clear the gesture history."""
        self.history.clear()