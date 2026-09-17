"""
Вспомогательный скрипт: нарезает 12 эталонов фигур + 1 эталон пустой клетки
из уже откалиброванной доски в НАЧАЛЬНОЙ позиции партии (когда точно известно,
что где стоит).

Запуск:
    1. Открой партию на chess24 в начальной позиции (либо сразу после старта).
    2. Убедись, что board_region.json уже создан (python capture.py --calibrate).
    3. Запусти: python generate_templates.py
    4. Скрипт сам вырежет все 64 клетки начальной позиции и разложит их
       по templates/ с правильными именами, т.к. начальная позиция известна
       заранее — можно не размечать руками.

После этого templates/ содержит:
    empty.png, wP.png, wN.png, wB.png, wR.png, wQ.png, wK.png,
    bP.png, bN.png, bB.png, bR.png, bQ.png, bK.png
(w/b = цвет, буква = тип фигуры, латинскими - как в FEN)
"""

import os
import cv2

from capture import grab_board, load_region
from boardgrid import split_into_cells

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

START_POSITION = [
    ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
    ["bP"] * 8,
    ["empty"] * 8,
    ["empty"] * 8,
    ["empty"] * 8,
    ["empty"] * 8,
    ["wP"] * 8,
    ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
]


def main():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    region = load_region()
    board_img = grab_board(region)
    cells = split_into_cells(board_img)

    saved = set()
    for row in range(8):
        for col in range(8):
            label = START_POSITION[row][col]
            if label == "empty":
                if "empty" in saved:
                    continue
            elif label in saved:
                continue
            path = os.path.join(TEMPLATES_DIR, f"{label}.png")
            cv2.imwrite(path, cells[row][col])
            saved.add(label)
            print(f"Сохранено: {path}")

    missing = {"empty", "wP", "wN", "wB", "wR", "wQ", "wK",
               "bP", "bN", "bB", "bR", "bQ", "bK"} - saved
    if missing:
        print(f"\nВНИМАНИЕ: не сохранены (в стартовой позиции их не было "
              f"в предсказуемом месте): {missing}")
        print("Дозаполни вручную - сделай скриншот доски с этими фигурами "
              "и вырежи клетку в любом графическом редакторе, сохрани как "
              "templates/<label>.png того же размера.")
    else:
        print("\nВсе 13 эталонов готовы.")


if __name__ == "__main__":
    main()
