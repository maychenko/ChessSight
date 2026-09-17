"""Тест Google Speech + нормализации голосовых шахматных координат."""

from voice_commands import listen_once, normalize_speech_text


if __name__ == "__main__":
    print("Говори координаты хода. Ctrl+C для выхода.\n")
    print("Примеры: 'бэ два бэ четыре', 'цэ семь цэ пять', 'и два и четыре'\n")

    while True:
        text = listen_once()
        if text:
            print(f">>> GOOGLE:       '{text}'")
            print(f">>> НОРМАЛИЗАЦИЯ: '{normalize_speech_text(text)}'\n")
        else:
            print(">>> (тишина / не разобрал)\n")
