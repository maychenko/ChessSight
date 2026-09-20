import cv2
import mediapipe as mp

from collections import deque

from gesture_classifier import (
    classify_gesture,
    GestureStabilizer
)

from gesture_controller import (
    GestureController
)


CAMERA_INDEX = 0

POSITION_HISTORY_SIZE = 5
SQUARE_STABLE_FRAMES = 3



def point_to_square(x, y):

    x = max(0.0, min(0.9999, x))
    y = max(0.0, min(0.9999, y))

    file_index = int(x * 8)
    row_index = int(y * 8)

    files = "abcdefgh"

    file_name = files[file_index]



    rank = 8 - row_index

    return f"{file_name}{rank}"



def average_position(points):

    if not points:
        return None

    x = sum(p[0] for p in points) / len(points)
    y = sum(p[1] for p in points) / len(points)

    return x, y



def get_palm_center(landmarks):

    ids = [
        0,   # wrist
        5,   # index MCP
        9,   # middle MCP
        13,  # ring MCP
        17   # pinky MCP
    ]

    x = sum(
        landmarks[i].x
        for i in ids
    ) / len(ids)

    y = sum(
        landmarks[i].y
        for i in ids
    ) / len(ids)

    return x, y



def get_index_tip(landmarks):

    point = landmarks[8]

    return point.x, point.y



mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)


cap = cv2.VideoCapture(
    CAMERA_INDEX,
    cv2.CAP_DSHOW
)

if not cap.isOpened():

    cap = cv2.VideoCapture(
        CAMERA_INDEX
    )

if not cap.isOpened():
    raise RuntimeError(
        "Камера не найдена."
    )


cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)



gesture_stabilizer = GestureStabilizer(
    size=5,
    required=3
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



print()
print("===================================")
print(" ChessSight - Gesture Position Test")
print("===================================")
print()

print("Управление:")
print("  ✊ = выбрать фигуру")
print("  ✌️ = двигать фигуру")
print("  🖐️ = подтвердить")
print("  ✌️ -> ✊ = отменить и выбрать другую")
print("  Q = выход")
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


    raw_gesture = "UNKNOWN"

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

        stable_gesture = gesture_stabilizer.update(
            raw_gesture
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


  
        finger_point = get_index_tip(
            landmarks
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


    else:

        stable_gesture = "UNKNOWN"


    controller_data = controller.update(
        stable_gesture,
        palm_square=palm_square,
        finger_square=finger_square
    )


    state = controller_data["state"]

    selected_square = controller_data["selected"]

    destination_square = controller_data["destination"]

    action = controller_data["action"]

    move = controller_data["move"]


    cv2.rectangle(
        frame,
        (15, 15),
        (700, 240),
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
        (30, 95),
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
        (30, 135),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Destination: {destination_text}",
        (30, 175),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 255),
        2
    )


    palm_text = (
        palm_square
        if palm_square
        else "---"
    )


    cv2.putText(
        frame,
        f"Palm: {palm_text}",
        (30, 210),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (200, 200, 200),
        2
    )


 
    if action:

        cv2.putText(
            frame,
            f"ACTION: {action}",
            (30, 245),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
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
        "ChessSight - Position Test",
        frame
    )


    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break



cap.release()

cv2.destroyAllWindows()

hands.close()

print()
print("Position test остановлен.")