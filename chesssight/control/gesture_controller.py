"""
gesture_controller.py

Controls the chess move selection state machine for gesture input.

The controller translates stabilized gestures and mapped chess squares
into a move-selection workflow:

    IDLE
      FIST
      ↓
    SELECTING
      FIST → change selected square
      TWO_FINGERS → start moving
      OPEN_PALM → cancel

    MOVING
      TWO_FINGERS → change destination square
      FIST → cancel movement and select another piece
      OPEN_PALM → confirm the move

The controller does not execute chess moves itself. It only returns a
confirmed pair of source and destination squares.
"""


class GestureController:
    """
    Manage the gesture-based chess move selection state machine.
    """

    def __init__(self):
        self.state = "IDLE"
        self.selected_square = None
        self.destination_square = None

    def reset(self):
        """Reset the controller to the initial IDLE state."""
        self.state = "IDLE"
        self.selected_square = None
        self.destination_square = None

    def update(
        self,
        gesture,
        palm_square,
        finger_square
    ):
        """
        Process a gesture and update the current move-selection state.

        Returns:
            None if no move has been confirmed.

            (from_square, to_square) when the user confirms a move
            with an open palm.
        """
        committed_move = None

        if self.state == "IDLE":
            self.selected_square = None
            self.destination_square = None

            if gesture == "FIST":
                if palm_square is not None:
                    self.selected_square = palm_square
                    self.state = "SELECTING"

        elif self.state == "SELECTING":
            if gesture == "FIST":
                if palm_square is not None:
                    self.selected_square = palm_square

            elif gesture == "TWO_FINGERS":
                if self.selected_square is not None:
                    self.destination_square = finger_square
                    self.state = "MOVING"

            elif gesture == "OPEN_PALM":
                self.reset()

        elif self.state == "MOVING":
            if gesture == "TWO_FINGERS":
                if finger_square is not None:
                    self.destination_square = finger_square

            elif gesture == "FIST":
                self.destination_square = None

                if palm_square is not None:
                    self.selected_square = palm_square
                    self.state = "SELECTING"
                else:
                    self.state = "SELECTING"

            elif gesture == "OPEN_PALM":
                if (
                    self.selected_square is not None
                    and self.destination_square is not None
                ):
                    committed_move = (
                        self.selected_square,
                        self.destination_square
                    )

                self.reset()

        return committed_move