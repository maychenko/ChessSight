"""
move_executor.py

Выполняет ход на экране: перетаскивает фигуру мышью с клетки на клетку
внутри откалиброванной области доски (board_region.json).

Требует pyautogui (добавлен в requirements.txt).
"""

import time
import chess
import pyautogui

pyautogui.PAUSE = 0.05


def square_to_pixel(square: str, region: dict, orientation="white_bottom"):
    """
    square: 'e4' и т.п.
    region: {'left','top','width','height'} - откалиброванный прямоугольник доски.
    Возвращает координаты центра клетки в системе координат ЭКРАНА (для pyautogui).
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

    x = region["left"] + col * cell_w + cell_w / 2
    y = region["top"] + row * cell_h + cell_h / 2
    return int(x), int(y)


def execute_move(move: chess.Move, region: dict, orientation="white_bottom"):
    """Перетаскивает фигуру: захват на from_square, перенос на to_square."""
    from_sq = chess.square_name(move.from_square)
    to_sq = chess.square_name(move.to_square)

    x1, y1 = square_to_pixel(from_sq, region, orientation)
    x2, y2 = square_to_pixel(to_sq, region, orientation)

    pyautogui.moveTo(x1, y1, duration=0.15)
    pyautogui.mouseDown()
    
    mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
    pyautogui.moveTo(mid_x, mid_y, duration=0.1)
    pyautogui.moveTo(x2, y2, duration=0.15)
    time.sleep(0.05)
    pyautogui.mouseUp()

    if move.promotion == chess.QUEEN:
        time.sleep(0.3)
        pyautogui.click(x2, y2)
