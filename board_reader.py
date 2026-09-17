"""
board_reader.py

Распознаёт изменение шахматной доски по двум снимкам.

Важно для chess.com/chess24:
подсветка последнего хода меняет цвет фона клетки, но фигура при этом
остаётся той же. Поэтому основной detector смотрит не только на RGB-разницу,
а на структуру фигуры (edges/границы). Это сильно уменьшает влияние
жёлто-зелёной подсветки.

Дополнительно infer_move_from_diff допускает лишние изменившиеся клетки.
Это нужно на случай, когда сайт одновременно убирает старую подсветку и
ставит новую: например реальный ход f7-f6 может визуально дать
{c2, c4, f7, f6}. Если f7/f6 соответствуют одному легальному ходу,
лишние клетки считаются подсветкой, а не частью хода.
"""

import os
import glob
import cv2
import numpy as np
import chess

from boardgrid import split_into_cells

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Порог для edge-based detector. Его лучше смотреть по debug-выводу.
EDGE_DIFF_THRESHOLD = 4.0

# Допустимое количество "лишних" клеток вокруг настоящего хода.
MAX_EXTRA_CHANGED = 4

# Сколько последовательных кадров должны подтверждать один и тот же ход.
STABLE_MOVE_FRAMES = 2


def load_templates():
    templates = {}
    for path in glob.glob(os.path.join(TEMPLATES_DIR, "*.png")):
        label = os.path.splitext(os.path.basename(path))[0]
        img = cv2.imread(path)
        if img is not None:
            templates[label] = img
    if not templates:
        raise RuntimeError(
            "Папка templates/ пуста или не читается. Запусти generate_templates.py."
        )
    return templates


def classify_cell(cell_img, templates):
    """Сравнивает клетку с эталонами по среднему пиксельному отличию."""
    best_label, best_score = None, None
    h, w = cell_img.shape[:2]
    for label, tmpl in templates.items():
        tmpl_resized = cv2.resize(tmpl, (w, h))
        diff = cv2.absdiff(cell_img, tmpl_resized)
        score = float(np.mean(diff))
        if best_score is None or score < best_score:
            best_label, best_score = label, score
    return best_label


def board_to_grid(board_img, templates):
    cells = split_into_cells(board_img)
    return [[classify_cell(c, templates) for c in row] for row in cells]


def _crop_cell(cell):
    """Убирает края клетки, где есть границы/координаты/артефакты интерфейса."""
    h, w = cell.shape[:2]
    y1, y2 = int(h * 0.08), int(h * 0.92)
    x1, x2 = int(w * 0.08), int(w * 0.92)
    return cell[y1:y2, x1:x2]


def _edge_map(cell):
    """Получает устойчивую к цвету фона карту контуров."""
    cell = _crop_cell(cell)
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    # Лёгкое сглаживание убирает шум от антиалиасинга/скриншота.
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, 45, 130)

    # Немного закрываем разрывы контуров фигур.
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    return edges


def cell_edge_diff_score(cell_a, cell_b):
    """Разница структуры клетки, почти не зависящая от цвета фона."""
    h, w = cell_a.shape[:2]
    cell_b = cv2.resize(cell_b, (w, h))

    a = _edge_map(cell_a)
    b = _edge_map(cell_b)

    # Доля пикселей, у которых контур изменился.
    return float(np.mean(cv2.absdiff(a, b)) / 255.0 * 100.0)


def cell_color_diff_score(cell_a, cell_b):
    """Старый RGB-like detector — оставлен как дополнительный debug-сигнал."""
    h, w = cell_a.shape[:2]
    cell_b = cv2.resize(cell_b, (w, h))
    a = _crop_cell(cell_a)
    b = _crop_cell(cell_b)
    return float(np.mean(cv2.absdiff(a, b)))


def cell_diff_score(cell_a, cell_b):
    """Основной score: изменение формы/контуров фигуры."""
    return cell_edge_diff_score(cell_a, cell_b)


def grid_to_square(row, col, orientation="white_bottom"):
    """row/col на изображении -> шахматная клетка a1-h8."""
    if orientation == "white_bottom":
        file_idx = col
        rank_idx = 7 - row
    else:
        file_idx = 7 - col
        rank_idx = row
    return f"{'abcdefgh'[file_idx]}{rank_idx + 1}"


def changed_squares(prev_board_img, curr_board_img, orientation="white_bottom", debug=False):
    """
    Возвращает множество клеток, где изменилась структура фигуры.

    Для debug=True печатает score каждой изменившейся клетки.
    """
    prev_cells = split_into_cells(prev_board_img)
    curr_cells = split_into_cells(curr_board_img)
    changed = set()

    for row in range(8):
        for col in range(8):
            edge_score = cell_edge_diff_score(prev_cells[row][col], curr_cells[row][col])
            color_score = cell_color_diff_score(prev_cells[row][col], curr_cells[row][col])

            if edge_score > EDGE_DIFF_THRESHOLD:
                square = grid_to_square(row, col, orientation)
                changed.add(square)
                if debug:
                    print(
                        f"[CV] {square}: edge={edge_score:.2f} color={color_score:.1f}"
                    )

    if debug and changed:
        print("[CV] Изменились:", ", ".join(sorted(changed)))

    return changed


def squares_touched_by_move(board: chess.Board, move: chess.Move):
    """Клетки, которые физически меняются при выполнении move."""
    touched = {
        chess.square_name(move.from_square),
        chess.square_name(move.to_square),
    }

    if board.is_en_passant(move):
        ep_square = move.to_square + (-8 if board.turn == chess.WHITE else 8)
        touched.add(chess.square_name(ep_square))

    if board.is_castling(move):
        if board.is_kingside_castling(move):
            rook_from = chess.H1 if board.turn == chess.WHITE else chess.H8
            rook_to = chess.F1 if board.turn == chess.WHITE else chess.F8
        else:
            rook_from = chess.A1 if board.turn == chess.WHITE else chess.A8
            rook_to = chess.D1 if board.turn == chess.WHITE else chess.D8
        touched.add(chess.square_name(rook_from))
        touched.add(chess.square_name(rook_to))

    return touched


def _move_name(move):
    return chess.square_name(move.from_square) + chess.square_name(move.to_square)


def infer_move_candidates(board: chess.Board, changed):
    """
    Возвращает кандидатов в формате:
        (move, extra_count)

    Сначала ищем идеальное совпадение.
    Если его нет, разрешаем лишние клетки (обычно это подсветка прошлого хода).
    """
    if not changed:
        return []

    candidates = []
    for move in board.legal_moves:
        touched = squares_touched_by_move(board, move)

        # Все реальные клетки хода должны присутствовать среди изменений.
        if not touched.issubset(changed):
            continue

        extra = len(changed - touched)
        if extra <= MAX_EXTRA_CHANGED:
            candidates.append((move, extra))

    # Сначала минимальное число лишних клеток.
    candidates.sort(key=lambda item: item[1])
    return candidates


def infer_move_from_diff(board: chess.Board, changed, debug=True):
    """Выбирает наиболее правдоподобный легальный ход."""
    candidates = infer_move_candidates(board, changed)

    if not candidates:
        if debug:
            print("[CV] Подходящих легальных ходов нет.")
        return None

    best_extra = candidates[0][1]
    best = [m for m, extra in candidates if extra == best_extra]

    if debug:
        preview = ", ".join(
            f"{_move_name(m)} (+{extra})" for m, extra in candidates[:8]
        )
        print(f"[CV] Кандидаты: {preview}")

    # Если несколько ходов одинаково хорошо подходят, не гадаем.
    if len(best) != 1:
        if debug:
            print("[CV] Неоднозначно — жду следующий стабильный кадр.")
        return None

    return best[0]
