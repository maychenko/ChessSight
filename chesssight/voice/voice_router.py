"""
voice_router.py

Runs background speech recognition for global mode switching.

The router is separate from gameplay voice commands.
It continuously listens for commands such as "жесты" and "голос"
and puts recognized text into a thread-safe queue.
"""

import threading
import queue

import speech_recognition as sr


def detect_mode_command(text):
    """Return the requested mode or None if no mode command is found."""

    if not text:
        return None

    text = text.lower().strip()

    text = text.replace(",", " ")
    text = text.replace(".", " ")
    text = " ".join(text.split())

    gesture_phrases = [
        "режим жестов",
        "режим жест",
        "режим жесто",
        "режим жес",
        "режим жэс",
        "жестовый режим",
        "жестовый",
        "жестами",
        "жесты",
        "жестов режим",
    ]

    for phrase in gesture_phrases:
        if phrase in text:
            return "GESTURE"

    voice_phrases = [
        "голосовой режим",
        "режим голоса",
        "режим голос",
        "голосовой",
        "голосом",
    ]

    for phrase in voice_phrases:
        if phrase in text:
            return "VOICE"

    return None


class VoiceRouter:
    """Listen for mode-switching commands in a background thread."""

    def __init__(self):
        self.recognizer = sr.Recognizer()

        self.microphone = None

        self.running = False

        self.thread = None

        self.commands = queue.Queue()

    def start(self):
        """Start the background voice-recognition thread."""

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

        print("[VOICE ROUTER] Запущен")

    def stop(self):
        """Stop the background voice-recognition thread."""

        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=1.0)

        print("[VOICE ROUTER] Остановлен")

    def get(self):
        """Return the next queued recognized command, if available."""

        try:
            return self.commands.get_nowait()

        except queue.Empty:
            return None

    def _run(self):
        """Run the continuous background speech-recognition loop."""

        try:
            print("[VOICE ROUTER] Настройка микрофона...")

            self.microphone = sr.Microphone()

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.7
                )

            print("[VOICE ROUTER] Готов")

        except Exception as e:
            print(
                f"[VOICE ROUTER] Ошибка микрофона: {e}"
            )

            self.running = False

            return

        while self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=1,
                        phrase_time_limit=4
                    )

                if not self.running:
                    break

                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language="ru-RU"
                    )

                    text = text.lower().strip()

                    if text:
                        print(
                            f"[VOICE ROUTER] Услышал: {text}"
                        )

                        self.commands.put(text)

                except sr.UnknownValueError:
                    pass

                except sr.RequestError as e:
                    print(
                        f"[VOICE ROUTER] "
                        f"Ошибка Google Speech: {e}"
                    )

            except sr.WaitTimeoutError:
                continue

            except Exception as e:
                if self.running:
                    print(
                        f"[VOICE ROUTER] Ошибка: {e}"
                    )