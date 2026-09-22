import json
import chess

from move_executor import execute_move


class GestureChess:

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
        ) as f:

            self.region = json.load(f)

        print(
            "[GESTURE CHESS] Board initialized"
        )

        print(
            "[GESTURE CHESS] "
            "Board region loaded"
        )

    def make_move(
        self,
        from_square,
        to_square
    ):

        uci = (
            f"{from_square}"
            f"{to_square}"
        )

        try:

            move = chess.Move.from_uci(
                uci
            )

        except ValueError:

            print(
                f"[GESTURE CHESS] "
                f"Invalid move: "
                f"{from_square} -> "
                f"{to_square}"
            )

            return False

        if move not in self.board.legal_moves:

            print(
                f"[GESTURE CHESS] "
                f"Illegal move: "
                f"{from_square} -> "
                f"{to_square}"
            )

            return False

        execute_move(
            move,
            self.region,
            self.orientation
        )

        self.board.push(move)

        print(
            f"[GESTURE CHESS] "
            f"Move executed: "
            f"{from_square} -> "
            f"{to_square}"
        )

        return True