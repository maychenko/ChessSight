# ChessSight

Chess bot for voice and gesture control.

ChessSight allows you to play chess on an online chessboard using your voice and hand gestures.

## Features

- Voice-controlled chess moves
- Voice commands for switching between control modes
- Hand gesture control
- Automatic opponent move detection
- Chess move validation with `python-chess`
- Mouse-based move execution
- Camera-based hand tracking with MediaPipe
- Visual gesture debugging
- Holographic overlay for gesture interaction

## Control Modes

### Voice Mode

Speak chess coordinates such as:

- `E2 E4`
- `B1 C3`
- `G7 G8`

ChessSight converts spoken coordinates into chess moves, validates them and executes legal moves on the board.

The voice system is designed for Russian speech while using standard chess coordinates from `a1` to `h8`.

### Gesture Mode

Hand gestures can be used to select and move pieces:

- ✊ **Fist** — select a piece
- ✌️ **Two fingers** — move the selected piece
- 🖐️ **Open palm** — confirm the move
- ✊ **Fist while moving** — cancel the current destination and select another piece

The camera tracks the hand using MediaPipe.

## Opponent Move Detection

ChessSight compares screenshots of the chessboard to detect changes after the opponent moves.

The detected changes are converted into possible chess moves and checked against the current `python-chess` board position.

Several stable frames are required before an opponent move is accepted.

## Technologies

- Python
- OpenCV
- MediaPipe
- python-chess
- SpeechRecognition
- Google Speech Recognition
- PyAutoGUI
- pywin32

## Project Structure

```text
ChessSight/
├── board/
│   └── board_reader.py
├── control/
│   ├── board_mapper.py
│   ├── gesture_classifier.py
│   └── gesture_controller.py
├── executor/
│   └── move_executor.py
├── gesture/
│   └── debug_overlay.py
├── input/
│   ├── camera.py
│   └── hand_tracker.py
├── ui/
│   └── holographic_overlay.py
├── voice/
│   ├── voice_commands.py
│   └── voice_router.py
├── main.py
├── board_region.json
└── requirements.txt
```

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Python 3.12 is used for development.

## Calibration

Before using the chessboard interaction, calibrate the board region:

```bash
python capture.py --calibrate
```

The calibration data is stored in:

```text
board_region.json
```

## Running

Start ChessSight with:

```bash
python main.py
```

You can choose your side:

```bash
python main.py --side white
```

or:

```bash
python main.py --side black
```

## Switching Modes

ChessSight starts in voice mode.

You can switch modes using voice commands:

```text
режим жестов
голосовой режим
```

## Status

ChessSight is a personal development project.

The main voice control, chess validation, screen move execution, opponent move detection and gesture control systems are implemented and are still being improved.