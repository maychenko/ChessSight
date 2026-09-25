"""
capture.py

Captures the screen and calibrates the chessboard position.

The board region is stored in board_region.json and is used by
the rest of ChessSight for screen capture, move execution and
opponent move detection.

Calibration:

    python capture.py --calibrate

Click the top-left corner of the chessboard first (a8), then the
bottom-right corner (h1).

The selected region is saved to board_region.json.
"""

import argparse
import json
import os

import cv2
import mss
import numpy as np


REGION_FILE = os.path.join(
    os.path.dirname(__file__),
    "board_region.json"
)

MIN_BOARD_SIZE = 100


def grab_full_screen():
    """Capture the primary monitor and return it as a BGR image."""

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = np.array(sct.grab(monitor))

        return cv2.cvtColor(
            raw,
            cv2.COLOR_BGRA2BGR
        )


def grab_board(region):
    """Capture the configured chessboard region from the screen."""

    with mss.mss() as sct:
        raw = np.array(sct.grab(region))

        return cv2.cvtColor(
            raw,
            cv2.COLOR_BGRA2BGR
        )


def load_region():
    """Load the calibrated chessboard region from board_region.json."""

    if not os.path.exists(REGION_FILE):
        raise FileNotFoundError(
            "Доска не откалибрована. "
            "Запусти: python capture.py --calibrate"
        )

    with open(REGION_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_region(region):
    """Save the calibrated chessboard region to board_region.json."""

    with open(
        REGION_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            region,
            f,
            indent=2
        )

    print(
        f"[калибровка] "
        f"Сохранено в {REGION_FILE}: {region}"
    )


def calibrate():
    """Interactively select and save the chessboard screen region."""

    frame = grab_full_screen()
    points = []

    window_name = (
        "Клик по левому-верхнему, потом "
        "правому-нижнему углу доски. "
        "ESC = отмена"
    )

    def on_click(event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        if len(points) >= 2:
            return

        points.append((x, y))

        print(
            f"Точка {len(points)}: ({x}, {y})"
        )

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL
    )

    cv2.setMouseCallback(
        window_name,
        on_click
    )

    while True:
        display = frame.copy()

        for index, point in enumerate(points):
            cv2.circle(
                display,
                point,
                6,
                (0, 0, 255),
                -1
            )

            cv2.putText(
                display,
                str(index + 1),
                (
                    point[0] + 10,
                    point[1] - 10
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        cv2.imshow(
            window_name,
            display
        )

        key = cv2.waitKey(20) & 0xFF

        if key == 27:
            print("[калибровка] Отменено.")
            cv2.destroyAllWindows()
            return

        if len(points) >= 2:
            break

    cv2.destroyAllWindows()

    (x1, y1), (x2, y2) = points

    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    if width < MIN_BOARD_SIZE or height < MIN_BOARD_SIZE:
        print(
            "[калибровка] Область слишком маленькая. "
            "Попробуй ещё раз."
        )
        return

    region = {
        "left": left,
        "top": top,
        "width": width,
        "height": height,
    }

    print()
    print("[калибровка] Новая область:")
    print(region)
    print()

    save_region(region)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--calibrate",
        action="store_true"
    )

    args = parser.parse_args()

    if args.calibrate:
        calibrate()
    else:
        print(
            "Используй: python capture.py --calibrate"
        )