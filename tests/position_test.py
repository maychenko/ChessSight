"""
position_test.py

Standalone test for gesture-based chess position control.

The script combines:
- MediaPipe hand tracking;
- gesture classification;
- hand-position smoothing;
- chess-square mapping;
- GestureController state management;
- GestureChess move validation and execution.

Supported controls:

FIST:
    Select a piece.

TWO_FINGERS:
    Move the selected piece.

OPEN_PALM:
    Confirm the move.

FIST while moving:
    Select another piece.

Q:
    Exit.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import mediapipe as mp
import math

from collections import deque, Counter

from chesssight.gesture.gesture_chess import GestureChess
from chesssight.control.gesture_classifier import classify_gesture
from chesssight.control.gesture_controller import GestureController


CAMERA_INDEX = 0

GESTURE_HISTORY_SIZE = 5
SQUARE_STABLE_FRAMES = 4
POSITION_HISTORY_SIZE = 5


mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)


def point_to_square(x, y):
    """Convert normalized camera coordinates into a chess square."""

    x = max(0.0, min(0.9999, x))
    y = max(0.0, min(0.9999, y))

    file_index = int(x * 8)
    row_index = int(y * 8)

    files = "abcdefgh"

    file_name = files[file_index]

    rank = 8 - row_index

    return f"{file_name}{rank}"


def average_position(points):
    """Return the average normalized position of recent points."""

    if not points:
        return None

    x = sum(p[0] for p in points) / len(points)
    y = sum(p[1] for p in points) / len(points)

    return x, y


def get_palm_center(landmarks):
    """Return the normalized center position of the palm."""

    ids = [0, 5, 9, 13, 17]

    x = sum(
        landmarks[i].x for i in ids
    ) / len(ids)

    y = sum(
        landmarks[i].y for i in ids
    ) / len(ids)

    return x, y


def get_stable_gesture(history):
    """Return the most frequent gesture from recent frames."""

    if not history:
        return "UNKNOWN"

    counts = Counter(history)

    gesture, count = counts.most_common(1)[0]

    if count >= 3:
        return gesture

    return "UNKNOWN"


def get_stable_square(square_history):
    """Return the most frequent square when it is stable enough."""

    if not square_history:
        return None

    counts = Counter(square_history)

    square, count = counts.most_common(1)[0]

    if count >= SQUARE_STABLE_FRAMES:
        return square

    return None


cap = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)

if not cap.isOpened():
    cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("Камера не найдена.")

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


gesture_history = deque(
    maxlen=GESTURE_HISTORY_SIZE
)

palm_positions = deque(
    maxlen=POSITION_HISTORY_SIZE
)

finger_positions = deque(
    maxlen=POSITION_HISTORY_SIZE
)

square_history = deque(
    maxlen=SQUARE_STABLE_FRAMES
)


controller = GestureController()
gesture_chess = GestureChess()


print()
print("===================================")
print(" ChessSight - Gesture Position Test")
print("===================================")
print()

print("Управление:")
print("  FIST        = выбрать фигуру")
print("  TWO_FINGERS = двигать фигуру")
print("  OPEN_PALM   = подтвердить")
print("  FIST        во время движения = выбрать другую")
print("  Q           = выход")
print()


while True:

    success, frame = cap.read()

    if not success:
        print("Не удалось получить кадр.")
        break

    frame = cv2.flip(frame, 1)

    height, width = frame.shape[:2]

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    result = hands.process(rgb)

    stable_gesture = "UNKNOWN"

    palm_square = None
    finger_square = None

    palm_point = None
    finger_point = None

    if result.multi_hand_landmarks:

        hand = result.multi_hand_landmarks[0]

        landmarks = hand.landmark

        mp_draw.draw_landmarks(
            frame,
            hand,
            mp_hands.HAND_CONNECTIONS
        )

        raw_gesture = classify_gesture(
            landmarks
        )

        gesture_history.append(
            raw_gesture
        )

        stable_gesture = get_stable_gesture(
            gesture_history
        )

        palm_point = get_palm_center(
            landmarks
        )

        palm_positions.append(
            palm_point
        )

        smooth_palm = average_position(
            palm_positions
        )

        if smooth_palm is not None:

            palm_x, palm_y = smooth_palm

            palm_square = point_to_square(
                palm_x,
                palm_y
            )

        index_tip = landmarks[8]

        finger_point = (
            index_tip.x,
            index_tip.y
        )

        finger_positions.append(
            finger_point
        )

        smooth_finger = average_position(
            finger_positions
        )

        if smooth_finger is not None:

            finger_x, finger_y = smooth_finger

            finger_square = point_to_square(
                finger_x,
                finger_y
            )

        if palm_point is not None:

            palm_px = int(
                palm_x * width
            )

            palm_py = int(
                palm_y * height
            )

            cv2.circle(
                frame,
                (palm_px, palm_py),
                10,
                (255, 0, 255),
                -1
            )

        if finger_point is not None:

            finger_px = int(
                finger_x * width
            )

            finger_py = int(
                finger_y * height
            )

            cv2.circle(
                frame,
                (finger_px, finger_py),
                12,
                (0, 255, 255),
                -1
            )

    else:

        gesture_history.clear()
        palm_positions.clear()
        finger_positions.clear()
        square_history.clear()

        stable_gesture = "UNKNOWN"

    committed_move = controller.update(
        stable_gesture,
        palm_square,
        finger_square
    )

    state = controller.state
    selected_square = controller.selected_square
    destination_square = controller.destination_square

    if committed_move is not None:

        from_square, to_square = committed_move

        print()
        print("===================================")
        print("MOVE COMMITTED")
        print(
            f"{from_square} -> {to_square}"
        )
        print("===================================")

        gesture_chess.make_move(
            from_square,
            to_square
        )

        print()

    cv2.rectangle(
        frame,
        (15, 15),
        (650, 220),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        f"Gesture: {stable_gesture}",
        (30, 55),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"State: {state}",
        (30, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2
    )

    selected_text = (
        selected_square
        if selected_square
        else "---"
    )

    destination_text = (
        destination_square
        if destination_square
        else "---"
    )

    cv2.putText(
        frame,
        f"Selected: {selected_text}",
        (30, 130),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Destination: {destination_text}",
        (30, 165),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )

    if palm_square:

        cv2.putText(
            frame,
            f"Palm: {palm_square}",
            (30, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (200, 200, 200),
            2
        )

    cv2.putText(
        frame,
        "Q - quit",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "ChessSight - Gesture Chess Controller",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


cap.release()

cv2.destroyAllWindows()

hands.close()

print()
print("Gesture test остановлен.")