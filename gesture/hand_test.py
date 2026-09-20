import cv2
import mediapipe as mp
import math
from collections import deque, Counter



CAMERA_INDEX = 0
MAX_HANDS = 1

STABLE_FRAMES = 5



mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=MAX_HANDS,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)



def distance(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2 +
        (a.y - b.y) ** 2 +
        (a.z - b.z) ** 2
    )


def angle(a, b, c):
    """
    Угол ABC.
    """
    ab = (
        a.x - b.x,
        a.y - b.y,
        a.z - b.z,
    )

    cb = (
        c.x - b.x,
        c.y - b.y,
        c.z - b.z,
    )

    dot = (
        ab[0] * cb[0]
        + ab[1] * cb[1]
        + ab[2] * cb[2]
    )

    len_ab = math.sqrt(
        ab[0] ** 2 +
        ab[1] ** 2 +
        ab[2] ** 2
    )

    len_cb = math.sqrt(
        cb[0] ** 2 +
        cb[1] ** 2 +
        cb[2] ** 2
    )

    if len_ab == 0 or len_cb == 0:
        return 0

    cos_value = dot / (len_ab * len_cb)

    
    cos_value = max(-1.0, min(1.0, cos_value))

    return math.degrees(math.acos(cos_value))


def finger_extended(landmarks, mcp, pip, dip, tip):
    """
    Определяем, выпрямлен ли палец.
    """
    a = landmarks[mcp]
    b = landmarks[pip]
    c = landmarks[dip]
    d = landmarks[tip]

    angle_pip = angle(a, b, c)
    angle_dip = angle(b, c, d)

    return angle_pip > 150 and angle_dip > 150


def classify_gesture(landmarks):
    """
    Возвращает:
        FIST
        TWO_FINGERS
        OPEN_PALM
        UNKNOWN
    """

    index = finger_extended(
        landmarks,
        5, 6, 7, 8
    )

    middle = finger_extended(
        landmarks,
        9, 10, 11, 12
    )

    ring = finger_extended(
        landmarks,
        13, 14, 15, 16
    )

    pinky = finger_extended(
        landmarks,
        17, 18, 19, 20
    )

    fingers = [index, middle, ring, pinky]

    # ✊
    # Все четыре основных пальца согнуты
    if not any(fingers):
        return "FIST"

    # ✌️
    # Указательный + средний вытянуты
    # Безымянный + мизинец согнуты
    if index and middle and not ring and not pinky:
        return "TWO_FINGERS"

    # 🖐️
    # Все четыре пальца вытянуты
    if all(fingers):
        return "OPEN_PALM"

    return "UNKNOWN"


def stable_gesture(history):
    """
    Берём наиболее частый жест
    из последних кадров.
    """

    if not history:
        return "UNKNOWN"

    counts = Counter(history)
    gesture, count = counts.most_common(1)[0]

    if count >= 3:
        return gesture

    return "UNKNOWN"



cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Не удалось открыть камеру.")
    print("Пробуем обычный режим...")

    cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    raise RuntimeError("Камера не найдена.")


cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


history = deque(maxlen=STABLE_FRAMES)


print("Камера запущена.")
print("Покажи руку.")
print("Q — выход.")



while True:

    success, frame = cap.read()

    if not success:
        print("Не удалось получить кадр.")
        break

    frame = cv2.flip(frame, 1)

  
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)

    raw_gesture = "UNKNOWN"

    if result.multi_hand_landmarks:

        hand_landmarks = result.multi_hand_landmarks[0]

      
        mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS
        )

        
        raw_gesture = classify_gesture(
            hand_landmarks.landmark
        )

    
    history.append(raw_gesture)

    gesture = stable_gesture(history)

  
    cv2.rectangle(
        frame,
        (20, 20),
        (430, 90),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        f"Gesture: {gesture}",
        (35, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Q - quit",
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow("ChessSight - Hand Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break



cap.release()
cv2.destroyAllWindows()
hands.close()

print("Камера остановлена.")