"""
move_executor.py

Executes chess moves on the screen using mouse input.

The module converts chess squares into screen coordinates based on the
calibrated board region and then performs a mouse drag from the source
square to the destination square.

The board region is expected to come from the calibrated
board_region.json configuration.

Move execution requires pyautogui.
"""

import time

import chess
import pyautogui


pyautogui.PAUSE = 0.05


def square_to_pixel(
    square: str,
    region: dict,
    orientation="white_bottom"
):
    """
    Convert a chess square into the screen coordinates of its center.

    Args:
        square: Chess square such as "e4".
        region: Calibrated board region containing left, top, width,
            and height.
        orientation: Board orientation. "white_bottom" means the white
            side is at the bottom of the screen.

    Returns:
        (x, y) screen coordinates suitable for pyautogui.
    """
    file_idx = "abcdefgh".index(square[0])
    rank_idx = int(square[1]) - 1

    cell_w = region["width"] / 8
    cell_h = region["height"] / 8

    if orientation == "white_bottom":
        col = file_idx
        row = 7 - rank_idx
    else:
        col = 7 - file_idx
        row = rank_idx

    x = (
        region["left"]
        + col * cell_w
        + cell_w / 2
    )

    y = (
        region["top"]
        + row * cell_h
        + cell_h / 2
    )

    return int(x), int(y)


def execute_move(
    move: chess.Move,
    region: dict,
    orientation="white_bottom"
):
    """
    Execute a chess move by dragging the piece on the screen.

    The mouse moves through the middle of the board before reaching the
    destination. For queen promotions, an additional click is performed
    after the drag to select the promoted piece.
    """
    from_sq = chess.square_name(move.from_square)
    to_sq = chess.square_name(move.to_square)

    x1, y1 = square_to_pixel(
        from_sq,
        region,
        orientation
    )

    x2, y2 = square_to_pixel(
        to_sq,
        region,
        orientation
    )

    pyautogui.moveTo(
        x1,
        y1,
        duration=0.15
    )

    pyautogui.mouseDown()

    mid_x = (x1 + x2) // 2
    mid_y = (y1 + y2) // 2

    pyautogui.moveTo(
        mid_x,
        mid_y,
        duration=0.1
    )

    pyautogui.moveTo(
        x2,
        y2,
        duration=0.15
    )

    time.sleep(0.05)

    pyautogui.mouseUp()

    if move.promotion == chess.QUEEN:
        time.sleep(0.3)
        pyautogui.click(x2, y2)