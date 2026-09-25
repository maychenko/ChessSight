"""
board_mapper.py

Maps hand positions from the camera's working area to chessboard squares.

The mapper uses a configurable rectangular working area and converts
pixel coordinates inside that area into standard chess coordinates such
as e2 or h7.
"""

import cv2


class BoardMapper:
    """Convert camera coordinates into chessboard coordinates."""

    def __init__(
        self,
        left=0,
        top=0,
        right=1280,
        bottom=720
    ):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def point_to_square(self, point):
        """
        Convert a pixel position into a chess square.

        Returns None when the point is outside the configured working
        area or when no valid chess square can be determined.
        """
        if point is None:
            return None

        x, y = point

        if x < self.left or x >= self.right:
            return None

        if y < self.top or y >= self.bottom:
            return None

        width = self.right - self.left
        height = self.bottom - self.top

        cell_width = width / 8
        cell_height = height / 8

        col = int((x - self.left) / cell_width)
        row = int((y - self.top) / cell_height)

        if not (0 <= col < 8 and 0 <= row < 8):
            return None

        file = "abcdefgh"[col]
        rank = 8 - row

        return f"{file}{rank}"

    def draw_board(self, frame):
        """
        Draw the 8x8 working-area grid on a camera frame.

        This is mainly useful for visualizing the coordinate mapping
        during gesture development and debugging.
        """
        for i in range(9):
            x = int(
                self.left
                + i * (self.right - self.left) / 8
            )

            cv2.line(
                frame,
                (x, self.top),
                (x, self.bottom),
                (80, 80, 80),
                1
            )

        for i in range(9):
            y = int(
                self.top
                + i * (self.bottom - self.top) / 8
            )

            cv2.line(
                frame,
                (self.left, y),
                (self.right, y),
                (80, 80, 80),
                1
            )

        return frame