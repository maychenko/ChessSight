"""
Захват экрана и калибровка положения доски.

ПОЧЕМУ КАЛИБРОВКА НУЖНА ОДИН РАЗ:
Доска на chess24 всегда в одном и том же месте окна, пока ты не двигаешь
окно/вкладку. Поэтому не нужно "искать" доску на каждом кадре — достаточно
один раз узнать её пиксельные координаты и потом просто вырезать тот же
прямоугольник из каждого нового скриншота. Это на порядок быстрее и надёжнее,
чем детекция доски заново каждый кадр.

Запуск калибровки:
    python capture.py --calibrate

Откроется окно со скриншотом экрана. Кликни ЛЕВОЙ кнопкой мыши сначала
в левый верхний угол доски (угол клетки a8), затем в правый нижний угол
доски (угол клетки h1). Координаты сохранятся в board_region.json.
"""

import json
import os
import argparse

import cv2
import mss
import numpy as np

REGION_FILE = os.path.join(os.path.dirname(__file__), "board_region.json")


def grab_full_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        raw = np.array(sct.grab(monitor))
        return cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)


def grab_board(region):
    """region: dict с left, top, width, height (пиксели экрана)."""
    with mss.mss() as sct:
        raw = np.array(sct.grab(region))
        return cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)


def load_region():
    if not os.path.exists(REGION_FILE):
        raise FileNotFoundError(
            "Доска не откалибрована. Запусти: python capture.py --calibrate"
        )
    with open(REGION_FILE) as f:
        return json.load(f)


def save_region(region):
    with open(REGION_FILE, "w") as f:
        json.dump(region, f, indent=2)
    print(f"[калибровка] Сохранено в {REGION_FILE}: {region}")


def calibrate():
    frame = grab_full_screen()
    points = []

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            print(f"Точка {len(points)}: ({x}, {y})")

    win = "Клик по левому-верхнему, потом правому-нижнему углу доски. ESC = отмена"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_click)

    while True:
        display = frame.copy()
        for p in points:
            cv2.circle(display, p, 6, (0, 0, 255), -1)
        cv2.imshow(win, display)
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
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()
    if args.calibrate:
        calibrate()
    else:
        print("Используй: python capture.py --calibrate")
