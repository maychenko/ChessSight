"""
debug_overlay.py

Draws a debug chessboard overlay on the camera frame.

The overlay is used only for visual debugging of gesture control.
It shows the virtual board coordinates, selected square, destination
square, movement direction, and current palm position.

This overlay is displayed inside the OpenCV camera window and does not
interact with the real chessboard on the screen.
"""

import cv2


class HolographicBoard:
    """Render a virtual chessboard for gesture interaction."""

    def __init__(
        self,
        left=680,
        top=80,
        size=560
    ):
        self.left = left
        self.top = top
        self.size = size

    @property
    def right(self):
        """Return the right screen coordinate of the board."""
        return self.left + self.size

    @property
    def bottom(self):
        """Return the bottom screen coordinate of the board."""
        return self.top + self.size

    def square_center(self, square):
        """
        Return the screen position of a chess square's center.

        The board uses the standard orientation with White at the bottom.
        """
        if not square:
            return None

        files = "abcdefgh"

        file_index = files.index(square[0])
        rank_index = int(square[1]) - 1

        cell = self.size / 8

        x = (
            self.left
            + file_index * cell
            + cell / 2
        )

        y = (
            self.top
            + (7 - rank_index) * cell
            + cell / 2
        )

        return int(x), int(y)

    def draw(self, frame, controller, palm_point=None):
        """
        Draw the board and current gesture-control state on a frame.

        The controller provides the selected and destination squares.
        The optional palm point is displayed as the current hand position.
        """
        cell = self.size / 8

        for i in range(9):
            x = int(self.left + i * cell)
            y = int(self.top + i * cell)

            cv2.line(
                frame,
                (x, self.top),
                (x, self.bottom),
                (100, 255, 255),
                1
            )

            cv2.line(
                frame,
                (self.left, y),
                (self.right, y),
                (100, 255, 255),
                1
            )

        for i, file_name in enumerate("abcdefgh"):
            x = int(
                self.left
                + i * cell
                + cell / 2
            )

            cv2.putText(
                frame,
                file_name,
                (x - 6, self.bottom + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 255, 255),
                1
            )

        for i in range(8):
            rank = 8 - i

            y = int(
                self.top
                + i * cell
                + cell / 2
            )

            cv2.putText(
                frame,
                str(rank),
                (self.left - 20, y + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (180, 255, 255),
                1
            )

        selected = controller.selected_square

        if selected:
            center = self.square_center(selected)

            if center:
                x, y = center

                cv2.rectangle(
                    frame,
                    (
                        int(x - cell / 2),
                        int(y - cell / 2)
                    ),
                    (
                        int(x + cell / 2),
                        int(y + cell / 2)
                    ),
                    (0, 255, 255),
                    4
                )

        destination = controller.destination_square

        if destination:
            center = self.square_center(destination)

            if center:
                x, y = center

                cv2.rectangle(
                    frame,
                    (
                        int(x - cell / 2),
                        int(y - cell / 2)
                    ),
                    (
                        int(x + cell / 2),
                        int(y + cell / 2)
                    ),
                    (0, 255, 0),
                    4
                )

        if selected and destination:
            start = self.square_center(selected)
            end = self.square_center(destination)

            if start and end:
                cv2.arrowedLine(
                    frame,
                    start,
                    end,
                    (0, 255, 255),
                    3,
                    tipLength=0.15
                )

        if palm_point:
            x, y = palm_point

            cv2.circle(
                frame,
                (int(x), int(y)),
                15,
                (255, 255, 255),
                3
            )

            cv2.circle(
                frame,
                (int(x), int(y)),
                4,
                (255, 255, 255),
                -1
            )

        return frame