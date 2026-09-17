"""
main.py
Голос -> проверка хода -> мышь.
CV ход противника подключается только в обычном режиме.
"""

import argparse
import time
import chess

from capture import grab_board, load_region
from board_reader import load_templates, changed_squares, infer_move_from_diff
from voice_commands import listen_once, parse_text_to_move
from move_executor import execute_move


def move_name(move):
    return f"{chess.square_name(move.from_square)}-{chess.square_name(move.to_square)}"


def wait_for_opponent_move(board, region, orientation, poll_interval=0.45, timeout=300):
    """
    Ждём ход противника.

    Сравниваем каждый новый кадр с одним и тем же кадром ДО хода.
    Поэтому после окончания анимации изменение остаётся видимым.
    """

    prev_img = grab_board(region)
    start = time.time()

    last_candidate = None
    stable_count = 0

    print("[CV] Слежу за доской...")

    while time.time() - start < timeout:
        time.sleep(poll_interval)

        curr_img = grab_board(region)

        diff = changed_squares(
            prev_img,
            curr_img,
            orientation,
            debug=True
        )

        if diff:
            move = infer_move_from_diff(
                board,
                diff,
                debug=True
            )

            if move is not None:

                if move == last_candidate:
                    stable_count += 1
                else:
                    last_candidate = move
                    stable_count = 1

                print(
                    f"[CV] Кандидат: {_move_name(move)} "
                    f"({stable_count}/{STABLE_MOVE_FRAMES})"
                )

                if stable_count >= STABLE_MOVE_FRAMES:
                    return move

            else:
                last_candidate = None
                stable_count = 0

        else:
            # ВАЖНО:
            # prev_img НЕ меняем.
            # Мы продолжаем сравнивать с состоянием ДО хода.
            pass

    return None


def human_turn(board):
    while True:
        text = listen_once()

        if not text:
            continue

        print(f"[голос] Услышал: {text}")

        move, error = parse_text_to_move(text, board)

        if move is None:
            print(f"[ошибка] {error}")
            continue

        print(f"[голос] Ход принят: {move_name(move)}")
        return move


def print_position(board):
    print("[позиция]")
    print(board)
    print(f"[позиция] FEN: {board.fen()}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--side",
        choices=["white", "black"],
        default="white"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="слушать голос и проверять ход, но не двигать мышь"
    )

    parser.add_argument(
        "--one-move",
        action="store_true",
        help="сделать один реальный ход мышью и завершить программу"
    )

    args = parser.parse_args()

    orientation = (
        "white_bottom"
        if args.side == "white"
        else "black_bottom"
    )

    my_color = (
        chess.WHITE
        if args.side == "white"
        else chess.BLACK
    )

    print("Партия началась.")
    print("Ориентация доски:", orientation)
    print(
        "Моя сторона:",
        "белые" if my_color == chess.WHITE else "чёрные"
    )

    if args.dry_run:
        print("Режим: DRY-RUN (без кликов)")

    if args.one_move:
        print("Режим: ONE-MOVE (один реальный ход)")

    # В dry-run экран вообще не нужен.
    if args.dry_run:
        region = None
    else:
        region = load_region()
        load_templates()

    board = chess.Board()

    print_position(board)

    # Если играем чёрными, первым ходит противник.
    if my_color == chess.BLACK and not args.dry_run:

        print("\nЖду первый ход противника...")

        move = wait_for_opponent_move(
            board,
            region,
            orientation
        )

        if move is None:
            print(
                "[ошибка] Не удалось распознать "
                "первый ход противника."
            )
            return

        board.push(move)

        print(
            f"[игра] Противник сыграл: "
            f"{move_name(move)}"
        )

        print_position(board)

    while not board.is_game_over():

        # --------------------------------
        # НАШ ХОД
        # --------------------------------
        if board.turn == my_color:

            print("\nТвой ход.")

            move = human_turn(board)

            # DRY RUN
            if args.dry_run:

                board.push(move)

                print("[dry-run] Мышь не двигаю.")

                print_position(board)

                # ВАЖНО:
                # dry-run заканчивается здесь.
                return

            # Реальный ход
            execute_move(
                move,
                region,
                orientation
            )

            board.push(move)

            print(
                f"[игра] Сыграно: "
                f"{move_name(move)}"
            )

            print_position(board)

            # Тест одного реального хода
            if args.one_move:

                print("[one-move] Готово.")

                return

            # Ждём окончания анимации
            time.sleep(0.5)

        # --------------------------------
        # ХОД ПРОТИВНИКА
        # --------------------------------
        else:

            print("\nЖду ход противника...")

            move = wait_for_opponent_move(
                board,
                region,
                orientation
            )

            if move is None:

                print(
                    "[внимание] "
                    "Ход противника не распознан."
                )

                continue

            board.push(move)

            print(
                f"[игра] Противник сыграл: "
                f"{move_name(move)}"
            )

            print_position(board)

    print(
        "Игра окончена:",
        board.result()
    )


if __name__ == "__main__":
    main()