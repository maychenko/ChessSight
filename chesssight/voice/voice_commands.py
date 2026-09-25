"""
voice_commands.py

Converts Russian speech into normalized chess coordinates and legal
chess.Move objects.

Chess files A-H are pronounced in Russian.

Google Speech may merge coordinates into a single token, for example:
    B224  -> b2 b4
    C75   -> c7 c5
    B2B4  -> b2 b4

The parser never guesses when there is not enough information.
"""

import re

import speech_recognition as sr
import chess


FILE_WORDS = {
    "а": "a", "эй": "a", "ей": "a",
    "бэ": "b", "бе": "b", "би": "b",
    "вэ": "b", "ве": "b", "ви": "b",
    "цэ": "c", "це": "c", "си": "c", "сэ": "c",
    "дэ": "d", "де": "d", "ди": "d",
    "и": "e", "э": "e", "е": "e",
    "эф": "f", "еф": "f",
    "джи": "g",
    "аш": "h", "эйч": "h",
}


NUMBER_WORDS = {
    "ноль": "0",
    "один": "1", "одна": "1",
    "два": "2", "две": "2",
    "три": "3",
    "четыре": "4",
    "пять": "5",
    "шесть": "6",
    "семь": "7",
    "восемь": "8",
}


SQUARE_RE = re.compile(
    r"(?<![a-h0-9])([a-h])\s*[-.,]?\s*([1-8])(?![0-9a-h])",
    re.IGNORECASE,
)


COMPACT_TWO_SQUARES_RE = re.compile(
    r"^([a-h])([1-8])([a-h])([1-8])$",
    re.IGNORECASE
)


COMPACT_SAME_FILE_RE = re.compile(
    r"^([a-h])([1-8])([1-8])$|^([a-h])([1-8])([1-8])([0-9]+)$",
    re.IGNORECASE,
)


def _replace_number_words(text: str) -> str:
    """Replace Russian number words with their digit equivalents."""

    for word, digit in sorted(
        NUMBER_WORDS.items(),
        key=lambda x: -len(x[0])
    ):
        text = re.sub(
            rf"(?<![а-яa-z]){re.escape(word)}(?![а-яa-z])",
            digit,
            text,
        )

    return text


def _replace_file_words(text: str) -> str:
    """Replace Russian chess-file words with Latin file letters."""

    for word, letter in sorted(
        FILE_WORDS.items(),
        key=lambda x: -len(x[0])
    ):
        text = re.sub(
            rf"(?<![а-яa-z]){re.escape(word)}(?![а-яa-z])",
            letter,
            text,
        )

    return text


def normalize_speech_text(text: str) -> str:
    """Normalize Google Speech output into stable chess-coordinate text."""

    text = text.lower().strip().replace("ё", "е")
    text = text.replace("—", "-").replace("–", "-")

    text = _replace_number_words(text)
    text = _replace_file_words(text)

    text = re.sub(
        r"(?<![a-zа-я])v(?=\s*[1-8]\b)",
        "b",
        text
    )

    text = re.sub(
        r"(?<![a-zа-я])в(?=\s*[1-8]\b)",
        "b",
        text
    )

    text = re.sub(
        r"(?<![a-zа-я])с(?=\s*[1-8]\b)",
        "c",
        text
    )

    text = re.sub(
        r"(?<![a-h0-9])([a-h][1-8])([a-h][1-8])(?![a-h0-9])",
        r"\1 \2",
        text,
    )

    text = re.sub(r"[,;:/]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_square(letter: str, digit: str) -> str:
    """Convert a file token and rank digit into a chess square name."""

    letter = FILE_WORDS.get(
        letter.lower(),
        letter.lower()
    )

    if letter == "в":
        letter = "b"
    elif letter == "с":
        letter = "c"

    return f"{letter}{digit}"


def _extract_squares(normalized: str):
    """Extract explicit chess squares from normalized speech."""

    return [
        normalize_square(letter, digit)
        for letter, digit in SQUARE_RE.findall(normalized)
    ]


def _compact_square_candidates(normalized: str):
    """
    Recover possible square pairs from a merged speech token.

    Examples:
        b224 -> b2,b4
        c75  -> c7,c5
        b2b4 -> b2,b4

    No guess is made for incomplete input such as B2B.
    """

    candidates = []

    tokens = re.findall(
        r"(?<![a-zа-я0-9])[a-z0-9]+(?![a-zа-я0-9])",
        normalized
    )

    for token in tokens:
        m = COMPACT_TWO_SQUARES_RE.fullmatch(token)

        if m:
            candidates.append(
                (
                    f"{m.group(1)}{m.group(2)}",
                    f"{m.group(3)}{m.group(4)}"
                )
            )
            continue

        m = re.fullmatch(
            r"([a-h])([1-8])([1-8])",
            token,
            re.IGNORECASE
        )

        if m:
            candidates.append(
                (
                    f"{m.group(1)}{m.group(2)}",
                    f"{m.group(1)}{m.group(3)}"
                )
            )

    return candidates


def _promotion_from_text(text: str):
    """Detect a requested promotion piece from spoken text."""

    if any(
        word in text
        for word in ("дам", "ферз", "королев", "queen")
    ):
        return chess.QUEEN

    if any(
        word in text
        for word in ("ладь", "rook")
    ):
        return chess.ROOK

    if any(
        word in text
        for word in ("слон", "bishop")
    ):
        return chess.BISHOP

    if any(
        word in text
        for word in ("кон", "knight")
    ):
        return chess.KNIGHT

    return None


def _legal_move(
    board: chess.Board,
    from_sq: str,
    to_sq: str,
    promotion=None
):
    """Create and validate a legal chess move."""

    try:
        from_square = chess.parse_square(from_sq)
        to_square = chess.parse_square(to_sq)
    except ValueError:
        return None

    move = chess.Move(
        from_square,
        to_square,
        promotion=promotion
    )

    if move in board.legal_moves:
        return move

    auto_promo = chess.Move(
        from_square,
        to_square,
        promotion=chess.QUEEN
    )

    if auto_promo in board.legal_moves:
        return auto_promo

    return None


def parse_text_to_move(text: str, board: chess.Board):
    """Parse spoken chess input into a legal chess.Move."""

    original = text
    normalized = normalize_speech_text(text)

    print(
        f"[голос] Нормализация: "
        f"'{original}' -> '{normalized}'"
    )

    if "рокировк" in normalized:
        want_short = "коротк" in normalized
        want_long = "длин" in normalized
        candidates = []

        for move in board.legal_moves:
            if not board.is_castling(move):
                continue

            if want_short and board.is_kingside_castling(move):
                candidates.append(move)

            elif want_long and board.is_queenside_castling(move):
                candidates.append(move)

            elif not want_short and not want_long:
                candidates.append(move)

        if len(candidates) == 1:
            return candidates[0], None

        if candidates and not want_short and not want_long:
            return None, "Скажи: короткая или длинная рокировка."

        return None, "Рокировка недоступна в этой позиции."

    promotion = _promotion_from_text(normalized)

    squares = _extract_squares(normalized)

    if len(squares) == 2:
        from_sq, to_sq = squares

        move = _legal_move(
            board,
            from_sq,
            to_sq,
            promotion
        )

        if move is not None:
            return move, None

        piece = board.piece_at(
            chess.parse_square(from_sq)
        )

        if piece is None:
            return None, (
                f"На клетке {from_sq} сейчас нет фигуры."
            )

        if piece.color != board.turn:
            side = (
                "белая"
                if piece.color == chess.WHITE
                else "чёрная"
            )

            return None, (
                f"На {from_sq} стоит {side} фигура, "
                f"но сейчас ход другой стороны."
            )

        return None, (
            f"Ход {from_sq}-{to_sq} "
            f"нелегален в текущей позиции."
        )

    if len(squares) > 2:
        return None, (
            f"Нашёл слишком много клеток: "
            f"{' '.join(squares)}. "
            f"Повтори только один ход."
        )

    compact_candidates = _compact_square_candidates(
        normalized
    )

    legal_candidates = []

    for from_sq, to_sq in compact_candidates:
        move = _legal_move(
            board,
            from_sq,
            to_sq,
            promotion
        )

        if move is not None and move not in legal_candidates:
            legal_candidates.append(move)

    if len(legal_candidates) == 1:
        move = legal_candidates[0]

        print(
            f"[голос] Восстановил склеенные координаты: "
            f"{chess.square_name(move.from_square)} "
            f"{chess.square_name(move.to_square)}"
        )

        return move, None

    if len(legal_candidates) > 1:
        return None, (
            "Нашёл несколько возможных ходов. "
            "Повтори координаты медленнее."
        )

    return None, (
        "Не понял две клетки. "
        "Повтори полностью, например: "
        "'бэ два бэ четыре'."
    )


def listen_once(
    recognizer=None,
    mic=None,
    language="ru-RU",
    timeout=6
):
    """Listen once and return the text recognized by Google Speech."""

    recognizer = recognizer or sr.Recognizer()
    mic = mic or sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.25
        )

        print("[голос] Слушаю...")

        try:
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=6
            )
        except sr.WaitTimeoutError:
            print("[голос] Время ожидания вышло.")
            return None

    try:
        result = recognizer.recognize_google(
            audio,
            language=language
        )

        print(
            f"[голос] Google: '{result}'"
        )

        return result

    except sr.UnknownValueError:
        print("[голос] Не разобрал речь.")
        return None

    except sr.RequestError as exc:
        print(
            f"[голос] Ошибка Google Speech API: {exc}"
        )
        return None