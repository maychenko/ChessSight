"""
board_reader.py

Detects changes on a chessboard by comparing two board screenshots.

The main detector compares the structure of chess pieces using edge maps
instead of relying only on pixel or color differences. This makes the
detector more resistant to last-move highlighting on chess.com and
chess24, where the square background can change while the piece itself
remains unchanged.

Move inference uses the current legal chess position. A detected change
does not have to match a move perfectly: a small number of additional
changed squares is allowed because UI highlighting can affect cells that
are not actually part of the move.

The module is responsible only for board image analysis and move
inference. It does not execute moves or control the game.
"""

import os
import glob

import cv2
import numpy as np
import chess

from chesssight.board.boardgrid import split_into_cells


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)

TEMPLATES_DIR = os.path.join(
    PROJECT_ROOT,
    "templates"
)

EDGE_DIFF_THRESHOLD = 4.0
MAX_EXTRA_CHANGED = 4
STABLE_MOVE_FRAMES = 2


def load_templates():
    """Load all chess-piece templates from the templates directory."""
    templates = {}

    for path in glob.glob(os.path.join(TEMPLATES_DIR, "*.png")):
        label = os.path.splitext(os.path.basename(path))[0]
        img = cv2.imread(path)

        if img is not None:
            templates[label] = img

    if not templates:
        raise RuntimeError(
            "The templates directory is empty or cannot be read. "
            "Run generate_templates.py first."
        )

    return templates


def classify_cell(cell_img, templates):
    """Classify a board cell by comparing it with the available templates."""
    best_label = None
    best_score = None

    height, width = cell_img.shape[:2]

    for label, template in templates.items():
        template_resized = cv2.resize(
            template,
            (width, height)
        )

        diff = cv2.absdiff(
            cell_img,
            template_resized
        )

        score = float(np.mean(diff))

        if best_score is None or score < best_score:
            best_label = label
            best_score = score

    return best_label


def board_to_grid(board_img, templates):
    """Convert a board image into an 8x8 grid of detected piece labels."""
    cells = split_into_cells(board_img)

    return [
        [
            classify_cell(cell, templates)
            for cell in row
        ]
        for row in cells
    ]


def _crop_cell(cell):
    """Remove the outer part of a cell where UI artifacts may appear."""
    height, width = cell.shape[:2]

    y1 = int(height * 0.08)
    y2 = int(height * 0.92)
    x1 = int(width * 0.08)
    x2 = int(width * 0.92)

    return cell[y1:y2, x1:x2]


def _edge_map(cell):
    """Create an edge map that is less sensitive to background color."""
    cell = _crop_cell(cell)
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    edges = cv2.Canny(
        gray,
        45,
        130
    )

    kernel = np.ones(
        (2, 2),
        np.uint8
    )

    return cv2.morphologyEx(
        edges,
        cv2.MORPH_CLOSE,
        kernel
    )


def cell_edge_diff_score(cell_a, cell_b):
    """Calculate the structural difference between two board cells."""
    height, width = cell_a.shape[:2]
    cell_b = cv2.resize(cell_b, (width, height))

    edges_a = _edge_map(cell_a)
    edges_b = _edge_map(cell_b)

    return float(
        np.mean(cv2.absdiff(edges_a, edges_b))
        / 255.0
        * 100.0
    )


def cell_color_diff_score(cell_a, cell_b):
    """Calculate the raw color difference between two board cells."""
    height, width = cell_a.shape[:2]
    cell_b = cv2.resize(cell_b, (width, height))

    cell_a = _crop_cell(cell_a)
    cell_b = _crop_cell(cell_b)

    return float(
        np.mean(cv2.absdiff(cell_a, cell_b))
    )


def cell_diff_score(cell_a, cell_b):
    """Return the main structural difference score for two cells."""
    return cell_edge_diff_score(cell_a, cell_b)


def grid_to_square(row, col, orientation="white_bottom"):
    """Convert an image grid position into a chess square name."""
    if orientation == "white_bottom":
        file_idx = col
        rank_idx = 7 - row
    else:
        file_idx = 7 - col
        rank_idx = row

    return f"{'abcdefgh'[file_idx]}{rank_idx + 1}"


def changed_squares(
    prev_board_img,
    curr_board_img,
    orientation="white_bottom",
    debug=False
):
    """
    Detect squares whose piece structure changed between two screenshots.

    When debug mode is enabled, the function prints the edge and color
    difference scores for changed squares.
    """
    prev_cells = split_into_cells(prev_board_img)
    curr_cells = split_into_cells(curr_board_img)

    changed = set()

    for row in range(8):
        for col in range(8):
            edge_score = cell_edge_diff_score(
                prev_cells[row][col],
                curr_cells[row][col]
            )

            color_score = cell_color_diff_score(
                prev_cells[row][col],
                curr_cells[row][col]
            )

            if edge_score > EDGE_DIFF_THRESHOLD:
                square = grid_to_square(
                    row,
                    col,
                    orientation
                )

                changed.add(square)

                if debug:
                    print(
                        f"[CV] {square}: "
                        f"edge={edge_score:.2f} "
                        f"color={color_score:.1f}"
                    )

    if debug and changed:
        print(
            "[CV] Changed squares:",
            ", ".join(sorted(changed))
        )

    return changed


def squares_touched_by_move(board: chess.Board, move: chess.Move):
    """
    Return all squares that physically change during a chess move.

    Handles normal moves, captures, en passant, and castling.
    """
    touched = {
        chess.square_name(move.from_square),
        chess.square_name(move.to_square),
    }

    if board.is_en_passant(move):
        ep_square = move.to_square + (
            -8 if board.turn == chess.WHITE else 8
        )

        touched.add(
            chess.square_name(ep_square)
        )

    if board.is_castling(move):
        if board.is_kingside_castling(move):
            rook_from = (
                chess.H1
                if board.turn == chess.WHITE
                else chess.H8
            )

            rook_to = (
                chess.F1
                if board.turn == chess.WHITE
                else chess.F8
            )
        else:
            rook_from = (
                chess.A1
                if board.turn == chess.WHITE
                else chess.A8
            )

            rook_to = (
                chess.D1
                if board.turn == chess.WHITE
                else chess.D8
            )

        touched.add(
            chess.square_name(rook_from)
        )

        touched.add(
            chess.square_name(rook_to)
        )

    return touched


def _move_name(move):
    """Return a compact coordinate representation of a chess move."""
    return (
        chess.square_name(move.from_square)
        + chess.square_name(move.to_square)
    )


def infer_move_candidates(board: chess.Board, changed):
    """
    Find legal moves that match the detected board changes.

    Returns pairs of:
        (move, extra_count)

    A move is accepted when all squares physically affected by the move
    are present in the detected changes. Additional changed squares are
    allowed because board highlighting may also modify the screenshot.
    """
    if not changed:
        return []

    candidates = []

    for move in board.legal_moves:
        touched = squares_touched_by_move(
            board,
            move
        )

        if not touched.issubset(changed):
            continue

        extra = len(changed - touched)

        if extra <= MAX_EXTRA_CHANGED:
            candidates.append(
                (move, extra)
            )

    candidates.sort(
        key=lambda item: item[1]
    )

    return candidates


def infer_move_from_diff(
    board: chess.Board,
    changed,
    debug=True
):
    """
    Infer one legal chess move from the detected changed squares.

    The move with the fewest additional changed squares is preferred.
    If several moves are equally plausible, no move is returned and the
    caller can wait for another stable frame.
    """
    candidates = infer_move_candidates(
        board,
        changed
    )

    if not candidates:
        if debug:
            print(
                "[CV] No matching legal moves found."
            )

        return None

    best_extra = candidates[0][1]

    best = [
        move
        for move, extra in candidates
        if extra == best_extra
    ]

    if debug:
        preview = ", ".join(
            f"{_move_name(move)} (+{extra})"
            for move, extra in candidates[:8]
        )

        print(
            f"[CV] Candidates: {preview}"
        )

    if len(best) != 1:
        if debug:
            print(
                "[CV] Ambiguous result. "
                "Waiting for another stable frame."
            )

        return None

    return best[0]