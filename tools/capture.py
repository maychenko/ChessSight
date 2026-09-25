"""
capture.py

Captures the screen and calibrates the chessboard position.

The board only needs to be calibrated once as long as the chessboard
stays in the same screen position.

After calibration, the program can capture the same rectangular region
from every new screenshot instead of detecting the board from scratch.

Calibration:

    python capture.py --calibrate

A screenshot of the screen is displayed. Click the top-left corner
of the board first (a8), then the bottom-right corner (h1).

The resulting coordinates are saved to board_region.json.
"""

import json
import os
import argparse

import cv2
import mss
import numpy as np


REGION_FILE = os.path.join(
    os.path.dirname(__file__),
    "board_region.json"
)


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
    """Capture the configured board region from the screen."""

    with mss.mss() as sct:
        raw = np.array(sct.grab(region))

        return cv2.cvtColor(
            raw,
            cv2.COLOR_BGRA2BGR
        )


def load_region():
    """Load the calibrated board region from board_region.json."""

    if not os.path.exists(REGION_FILE):
        raise FileNotFoundError(
            "Доска не откалибрована. "
            "Запусти: python capture.py --calibrate"
        )

    with open(REGION_FILE) as f:
        return json.load(f)


def save_region(region):
    """Save the calibrated board region to board_region.json."""

    with open(REGION_FILE, "w") as f:
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

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))

            print(
                f"Точка {len(points)}: ({x}, {y})"
            )

    win = (
        "Клик по левому-верхнему, потом "
        "правому-нижнему углу доски. ESC = отмена"
    )

    cv2.namedWindow(
        win,
        cv2.WINDOW_NORMAL
    )

    cv2.setMouseCallback(
        win,
        on_click
    )

    while True:
        display = frame.copy()

        for p in points:
            cv2.circle(
                display,
                p,
                6,
                (0, 0, 255),
                -1
            )

        cv2.imshow(
            win,
            display
        )

        key = cv2.waitKey(20) & 0xFF

        if key == 27:
            cv2.destroyAllWindows()
            return

        if len(points) >= 2:
            break

    cv2.destroyAllWindows()

    (x1, y1), (x2, y2) = points[0], points[1]

    region = {
        "left": min(x1, x2),
        "top": min(y1, y2),
        "width": abs(x2 - x1),
        "height": abs(y2 - y1),
    }

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