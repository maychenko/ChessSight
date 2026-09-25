"""
camera.py

Provides a small wrapper around OpenCV's camera interface.

The camera is opened with DirectShow on Windows when available and
automatically falls back to OpenCV's default backend.
"""

import cv2


class Camera:
    """Capture and preprocess frames from the webcam."""

    def __init__(
        self,
        index=0,
        width=1280,
        height=720
    ):
        self.cap = cv2.VideoCapture(
            index,
            cv2.CAP_DSHOW
        )

        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(index)

        if not self.cap.isOpened():
            raise RuntimeError(
                "Failed to open camera"
            )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            width
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            height
        )

    def read(self):
        """
        Capture and return the next camera frame.

        The frame is horizontally flipped so the camera behaves like
        a mirror during gesture interaction.

        Returns:
            The processed frame, or None if capture failed.
        """
        ok, frame = self.cap.read()

        if not ok:
            return None

        return cv2.flip(frame, 1)

    def release(self):
        """Release the camera device."""
        self.cap.release()