# CLI Car Race Game 🚗

A fast-paced, text-based terminal dodging game written in Python 3. It features non-blocking real-time keyboard inputs, adaptive difficulty, and cross-platform compatibility (Linux/macOS/Windows).

## 🌟 Features

- **Real-Time Inputs:** Smooth movement using `msvcrt` (Windows) and `termios/select` (Linux) without blocking the game thread.
- **Adaptive Difficulty:** The game accelerates automatically as your score increases.
- **Power-ups & Obstacles:** Dodge obstacles (`X`), collect temporary Shields (`S`), and grab Bonus points (`$`).
- **Persistent Highscore:** Saves your best performance locally in a `highscore.json` file.
- **Flicker-Free Rendering:** Optimized screen refreshing for a smooth terminal gameplay experience.

## 🕹️ Controls

- `a` : Move Left
- `d` : Move Right
- `q` : Quit Game instantly

## 🚀 How to Run

1. Clone this repository:
   ```bash
   git clone [https://github.com/Anonymous1055/cli-car-race.git]
