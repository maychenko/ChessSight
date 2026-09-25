"""
generate_templates.py

Creates reference images for all 12 chess piece types and one empty
square from a calibrated board in the starting position.

Usage:

1. Open a chess game in the starting position.
2. Make sure board_region.json has already been created.
3. Run:

       python -m tools.generate_templates

The script captures all 64 board cells and saves one example for each
known piece type and for an empty square.

The generated templates are:

    empty.png
    wP.png
    wN.png
    wB.png
    wR.png
    wQ.png
    wK.png
    bP.png
    bN.png
    bB.png
    bR.png
    bQ.png
    bK.png

w/b represent the piece color. The piece letters follow standard
FEN notation.
"""

import os

import cv2

from tools.capture import grab_board, load_region
from chesssight.board.boardgrid import split_into_cells


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(__file__)
)

TEMPLATES_DIR = os.path.join(
    PROJECT_ROOT,
    "templates"
)


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
    """Capture the starting board and generate all available templates."""

    os.makedirs(
        TEMPLATES_DIR,
        exist_ok=True
    )

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

            path = os.path.join(
                TEMPLATES_DIR,
                f"{label}.png"
            )

            cv2.imwrite(
                path,
                cells[row][col]
            )

            saved.add(label)

            print(
                f"Сохранено: {path}"
            )

    missing = {
        "empty",
        "wP", "wN", "wB", "wR", "wQ", "wK",
        "bP", "bN", "bB", "bR", "bQ", "bK"
    } - saved

    if missing:
        print(
            f"\nВНИМАНИЕ: не сохранены "
            f"(в стартовой позиции их не было "
            f"в предсказуемом месте): {missing}"
        )

        print(
            "Дозаполни вручную - сделай скриншот доски "
            "с этими фигурами и вырежи клетку в любом "
            "графическом редакторе, сохрани как "
            "templates/<label>.png того же размера."
        )

    else:
        print(
            "\nВсе 13 эталонов готовы."
        )


if __name__ == "__main__":
    main()