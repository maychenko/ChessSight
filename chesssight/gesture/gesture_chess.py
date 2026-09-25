"""
gesture_chess.py

Connects gesture-based move selection with the chess game state.

The class validates a proposed move using python-chess, executes the
move on the real chessboard through the mouse executor, and updates
the internal board position.
"""

import json

import chess

from chesssight.executor.move_executor import execute_move


class GestureChess:
    """Manage chess moves created through gesture control."""

    def __init__(
        self,
        board_region_path="board_region.json",
        orientation="white_bottom"
    ):
        self.board = chess.Board()
        self.orientation = orientation

        with open(
            board_region_path,
            "r",
            encoding="utf-8"
        ) as file:
            self.region = json.load(file)

        print("[GESTURE CHESS] Board initialized")
        print("[GESTURE CHESS] Board region loaded")

    def make_move(self, from_square, to_square):
        """
        Validate and execute a gesture-selected chess move.

        Returns:
            True if the move was valid and executed.
            False if the move was invalid or illegal.
        """
        uci = f"{from_square}{to_square}"

        try:
            move = chess.Move.from_uci(uci)

        except ValueError:
            print(
                f"[GESTURE CHESS] Invalid move: "
                f"{from_square} -> {to_square}"
            )
            return False

        if move not in self.board.legal_moves:
            print(
                f"[GESTURE CHESS] Illegal move: "
                f"{from_square} -> {to_square}"
            )
            return False

        execute_move(
            move,
            self.region,
            self.orientation
        )

        self.board.push(move)

        print(
            f"[GESTURE CHESS] Move executed: "
            f"{from_square} -> {to_square}"
        )

        return True