"""
main.py

Main entry point for ChessSight.

The program combines:
- voice chess control;
- background voice mode switching;
- gesture-based chess control;
- opponent move detection from board screenshots;
- screen move execution;
- debug and holographic overlays.

The active control mode can be switched between VOICE and GESTURE
using the background voice router.
"""

import argparse
import time

import cv2
import chess

from tools.capture import grab_board, load_region

from chesssight.board.board_reader import (
    load_templates,
    changed_squares,
    infer_move_from_diff,
    STABLE_MOVE_FRAMES,
)

from chesssight.voice.voice_commands import parse_text_to_move
from chesssight.executor.move_executor import execute_move

from chesssight.voice.voice_router import (
    VoiceRouter,
    detect_mode_command,
)

from chesssight.input.camera import Camera
from chesssight.input.hand_tracker import HandTracker
from chesssight.control.gesture_classifier import classify_gesture
from chesssight.control.board_mapper import BoardMapper
from chesssight.control.gesture_controller import GestureController
from chesssight.gesture.debug_overlay import HolographicBoard
from chesssight.ui.holographic_overlay import HolographicOverlay


def move_name(move):
    """Return a readable chess move such as e2-e4."""

    return (
        f"{chess.square_name(move.from_square)}"
        f"-"
        f"{chess.square_name(move.to_square)}"
    )


class GestureRuntime:
    """Manage camera-based gesture control during GESTURE mode."""

    def __init__(self, board_region, holographic_overlay):
        self.camera = Camera()
        self.tracker = HandTracker()

        self.mapper = BoardMapper(
            left=430,
            top=170,
            right=850,
            bottom=590
        )

        self.controller = GestureController()
        self.debug_board = HolographicBoard()

        self.holographic_overlay = holographic_overlay

        self.gesture_history = []
        self.history_size = 5

    def reset(self):
        """Reset gesture state and clear the holographic overlay."""

        self.controller.reset()
        self.gesture_history.clear()

        if self.holographic_overlay:
            self.holographic_overlay.clear()

    def close(self):
        """Release camera and hand-tracking resources."""

        self.camera.release()
        self.tracker.close()

    def stable_gesture(self, gesture):
        """Return the most frequent gesture from the recent history."""

        self.gesture_history.append(gesture)

        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)

        if not self.gesture_history:
            return "UNKNOWN"

        counts = {}

        for item in self.gesture_history:
            counts[item] = counts.get(item, 0) + 1

        return max(
            self.gesture_history,
            key=self.gesture_history.count
        )

    def update(self):
        """
        Process one camera frame and update gesture control.

        Returns:
            tuple:
                processed camera frame,
                committed move or None.
        """

        frame = self.camera.read()

        if frame is None:
            return None, None

        landmarks = self.tracker.process(frame)

        gesture = "UNKNOWN"
        stable_gesture = "UNKNOWN"

        palm_square = None
        finger_square = None

        palm_point = None
        finger_point = None

        committed_move = None

        if landmarks is not None:

            self.tracker.draw(frame, landmarks)

            gesture = classify_gesture(landmarks)

            stable_gesture = self.stable_gesture(gesture)

            palm = self.tracker.get_palm_position(landmarks)

            if palm is not None:
                h, w = frame.shape[:2]

                palm_point = (
                    int(palm[0] * w),
                    int(palm[1] * h)
                )

                palm_square = self.mapper.point_to_square(
                    palm_point
                )

            finger = self.tracker.get_finger_position(landmarks)

            if finger is not None:
                h, w = frame.shape[:2]

                finger_point = (
                    int(finger[0] * w),
                    int(finger[1] * h)
                )

                finger_square = self.mapper.point_to_square(
                    finger_point
                )

            committed_move = self.controller.update(
                stable_gesture,
                palm_square,
                finger_square
            )

        else:
            self.gesture_history.clear()

        cv2.rectangle(
            frame,
            (10, 10),
            (640, 220),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            frame,
            f"GESTURE: {gesture}",
            (25, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"STABLE: {stable_gesture}",
            (25, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"STATE: {self.controller.state}",
            (25, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"PALM: {palm_square or '---'}",
            (25, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"FINGER: {finger_square or '---'}",
            (25, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "MODE: GESTURE",
            (25, 215),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (100, 255, 255),
            2
        )

        frame = self.debug_board.draw(
            frame,
            self.controller,
            palm_point
        )

        current_square = None

        if stable_gesture == "FIST":
            current_square = palm_square

        elif stable_gesture == "TWO_FINGERS":
            current_square = finger_square

        else:
            current_square = finger_square or palm_square

        if self.holographic_overlay:
            self.holographic_overlay.draw(
                selected_square=self.controller.selected_square,
                destination_square=self.controller.destination_square,
                current_square=current_square,
                gesture=stable_gesture,
                show_grid=False
            )

        return frame, committed_move


class OpponentMoveDetector:
    """Detect and stabilize the opponent's move from board screenshots."""

    def __init__(
        self,
        region,
        orientation,
        poll_interval=0.45
    ):
        self.region = region
        self.orientation = orientation
        self.poll_interval = poll_interval

        self.active = False
        self.base_img = None

        self.last_poll = 0.0
        self.last_candidate = None
        self.stable_count = 0

    def start(self):
        """Start monitoring the board from a new baseline screenshot."""

        if self.active:
            return

        self.base_img = grab_board(self.region)

        self.last_poll = 0.0
        self.last_candidate = None
        self.stable_count = 0

        self.active = True

        print("[CV] Слежу за доской...")

    def stop(self):
        """Stop board monitoring and clear the current detection state."""

        self.active = False

        self.base_img = None
        self.last_candidate = None
        self.stable_count = 0

    def update(self, board):
        """
        Check the board for an opponent move.

        Returns:
            A detected chess.Move after it remains stable for the
            configured number of frames, otherwise None.
        """

        if not self.active:
            return None

        if self.base_img is None:
            self.start()
            return None

        now = time.monotonic()

        if now - self.last_poll < self.poll_interval:
            return None

        self.last_poll = now

        curr_img = grab_board(self.region)

        diff = changed_squares(
            self.base_img,
            curr_img,
            self.orientation,
            debug=False
        )

        if diff:

            move = infer_move_from_diff(
                board,
                diff,
                debug=False
            )

            if move is not None:

                if move == self.last_candidate:
                    self.stable_count += 1

                else:
                    self.last_candidate = move
                    self.stable_count = 1

                print(
                    f"[CV] Кандидат: {move_name(move)} "
                    f"({self.stable_count}/{STABLE_MOVE_FRAMES})"
                )

                if self.stable_count >= STABLE_MOVE_FRAMES:

                    self.stop()

                    return move

            else:
                self.last_candidate = None
                self.stable_count = 0

        return None


def main():
    """Initialize ChessSight and run the main game loop."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--side",
        choices=["white", "black"],
        default="white"
    )

    args = parser.parse_args()

    orientation = (
        "white_bottom"
        if args.side == "white"
        else "black_bottom"
    )

    my_color = (
        chess.WHITE
        if args.side == "white"
        else chess.BLACK
    )

    region = load_region()

    load_templates()

    board = chess.Board()

    mode_state = {
        "mode": "VOICE"
    }

    voice_router = VoiceRouter()
    voice_router.start()

    holographic_overlay = HolographicOverlay(region)

    gesture_runtime = None

    opponent_detector = OpponentMoveDetector(
        region,
        orientation
    )

    print()
    print("======================================")
    print("          ChessSight")
    print("======================================")
    print()
    print("MODE: VOICE")
    print()
    print("Голосовые переключатели:")
    print("  'режим жестов'")
    print("  'голосовой режим'")
    print()
    print("Q в окне камеры = выход")
    print()

    try:

        while not board.is_game_over():

            while True:

                text = voice_router.get()

                if text is None:
                    break

                command = detect_mode_command(text)

                if command:

                    if command != mode_state["mode"]:

                        mode_state["mode"] = command

                        print()
                        print(
                            f"[MODE] Переключение -> {command}"
                        )
                        print()

                        if command == "GESTURE":

                            if gesture_runtime is None:

                                gesture_runtime = GestureRuntime(
                                    region,
                                    holographic_overlay
                                )

                            gesture_runtime.reset()

                            if hasattr(
                                holographic_overlay,
                                "show"
                            ):
                                holographic_overlay.show()

                        else:

                            if gesture_runtime is not None:
                                gesture_runtime.reset()

                            if hasattr(
                                holographic_overlay,
                                "hide"
                            ):
                                holographic_overlay.hide()

                            else:
                                holographic_overlay.clear()

                    continue

                if (
                    mode_state["mode"] == "VOICE"
                    and board.turn == my_color
                ):

                    move, error = parse_text_to_move(
                        text,
                        board
                    )

                    if move is None:

                        print(
                            f"[ошибка] {error}"
                        )

                    else:

                        execute_move(
                            move,
                            region,
                            orientation
                        )

                        board.push(move)

                        print(
                            f"[игра] Сыграно: "
                            f"{move_name(move)}"
                        )

                        time.sleep(0.35)

            if mode_state["mode"] == "GESTURE":

                if gesture_runtime is None:

                    gesture_runtime = GestureRuntime(
                        region,
                        holographic_overlay
                    )

                frame, committed_move = (
                    gesture_runtime.update()
                )

                if frame is not None:

                    cv2.imshow(
                        "ChessSight - Gesture Mode",
                        frame
                    )

                if committed_move:

                    from_square, to_square = committed_move

                    try:

                        move = chess.Move.from_uci(
                            from_square + to_square
                        )

                    except ValueError:

                        move = None

                    if move is None:

                        print(
                            "[GESTURE] Некорректный ход"
                        )

                    elif board.turn != my_color:

                        print(
                            "[GESTURE] Сейчас ход противника"
                        )

                    elif move not in board.legal_moves:

                        print(
                            f"[GESTURE] Illegal move: "
                            f"{from_square} -> {to_square}"
                        )

                    else:

                        execute_move(
                            move,
                            region,
                            orientation
                        )

                        board.push(move)

                        print(
                            f"[GESTURE] Сыграно: "
                            f"{move_name(move)}"
                        )

                        time.sleep(0.35)

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    break

            if board.turn != my_color:

                opponent_detector.start()

                move = opponent_detector.update(
                    board
                )

                if move is not None:

                    board.push(move)

                    print(
                        f"[игра] Противник сыграл: "
                        f"{move_name(move)}"
                    )

            else:

                opponent_detector.stop()

            time.sleep(0.01)

    finally:

        opponent_detector.stop()

        voice_router.stop()

        if gesture_runtime is not None:
            gesture_runtime.close()

        if holographic_overlay is not None:
            holographic_overlay.close()

        cv2.destroyAllWindows()

    print()
    print("ChessSight остановлен.")


if __name__ == "__main__":
    main()