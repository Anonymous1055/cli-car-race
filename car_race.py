"""
CAR RACE - A text-based dodging game
Dodge obstacles, collect power-ups, survive as long as possible.
Optimized & Fixed Version
"""
# By @Anonymous1055
import random
import time
import os
import json
import sys

# Non-blocking input support depending on OS
if os.name == 'nt':
    import msvcrt
else:
    import select
    import tty
    import termios

HIGHSCORE_FILE = "highscore.json"
LANES = 3
ROAD_HEIGHT = 8  # Visible length of the road

# --------------------------------------------------------------------------- #
# Utility functions
# --------------------------------------------------------------------------- #
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                data = json.load(f)
                return data.get("highscore", 0)
        except (json.JSONDecodeError, IOError):
            return 0
    return 0

def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            json.dump({"highscore": score}, f)
    except IOError:
        print("Error saving highscore.")

def print_header(title):
    print("=" * 40)
    print(title.center(40))
    print("=" * 40)

# --------------------------------------------------------------------------- #
# Terminal raw-mode handling (POSIX only)
# Set ONCE per game session instead of on every keystroke poll.
# Uses setcbreak (not setraw) so Ctrl+C / SIGINT still works.
# --------------------------------------------------------------------------- #
class TerminalMode:
    def __init__(self):
        self.fd = None
        self.old_settings = None

    def __enter__(self):
        if os.name != 'nt':
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.name != 'nt' and self.old_settings is not None:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

def get_key_async():
    if os.name == 'nt':
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore').lower()
        return None
    else:
        rlist, _, _ = select.select([sys.stdin], [], [], 0)
        if rlist:
            return sys.stdin.read(1).lower()
        return None

# --------------------------------------------------------------------------- #
# Game state
# --------------------------------------------------------------------------- #
class GameState:
    def __init__(self, difficulty="normal"):
        self.car_lane = 1
        self.score = 0
        self.lives = 3
        self.row_history = [(-1, ".") for _ in range(ROAD_HEIGHT)]
        self.shield_active = False
        self.shield_timer = 0
        self.difficulty = difficulty
        self.speed = self._base_speed()
        self.min_speed = self._min_speed()

    def _base_speed(self):
        return {"easy": 0.5, "normal": 0.35, "hard": 0.2}.get(self.difficulty, 0.35)

    def _min_speed(self):
        return {"easy": 0.25, "normal": 0.15, "hard": 0.08}.get(self.difficulty, 0.15)

    def increase_difficulty(self):
        if self.score > 0 and self.score % 5 == 0 and self.speed > self.min_speed:
            self.speed = round(self.speed - 0.02, 3)

    def tick_shield(self):
        # Decrement first, then check — cleaner than checking-then-decrementing
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

# --------------------------------------------------------------------------- #
# Obstacle / power-up generation
# --------------------------------------------------------------------------- #
OBSTACLE = "X"
POWERUP_SHIELD = "S"
POWERUP_SCORE = "$"
EMPTY = "."

def generate_row():
    roll = random.random()
    lane = random.randint(0, LANES - 1)
    if roll < 0.25:
        return (lane, OBSTACLE)
    elif roll < 0.30:
        return (lane, POWERUP_SHIELD)
    elif roll < 0.35:
        return (lane, POWERUP_SCORE)
    else:
        return (-1, EMPTY)

# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render(state, message=""):
    clear()
    print_header("CAR RACE")
    shield_status = f"ON ({state.shield_timer}s)" if state.shield_active else "OFF"
    print(f"Score: {state.score} | Lives: {'❤️ ' * state.lives} | Shield: {shield_status}")
    print("-" * 40)

    for lane_idx, symbol in state.row_history:
        row = ""
        for lane in range(LANES):
            row += f" {symbol} " if lane == lane_idx else " . "
        print(row.center(40))

    car_line = ""
    for lane in range(LANES):
        car_line += " 🚗" if lane == state.car_lane else " . "
    print(car_line.center(40))
    print("-" * 40)
    print("[a] left   [d] right   [q] quit")

    if message:
        print(message.center(40))

# --------------------------------------------------------------------------- #
# Collision handling
# --------------------------------------------------------------------------- #
def handle_collision(state, lane_idx, symbol):
    if lane_idx != state.car_lane:
        return True, ""

    if symbol == OBSTACLE:
        if state.shield_active:
            state.shield_active = False
            state.shield_timer = 0
            return True, "🛡️ Shield absorbed the hit!"
        else:
            state.lives -= 1
            if state.lives <= 0:
                return False, "💥 Crash!"
            return True, "💥 Crash!"
    elif symbol == POWERUP_SHIELD:
        state.shield_active = True
        state.shield_timer = 10
        return True, "🛡️ Shield activated!"
    elif symbol == POWERUP_SCORE:
        state.score += 5
        return True, "💰 Bonus points!"

    return True, ""

# --------------------------------------------------------------------------- #
# Main game loop
# --------------------------------------------------------------------------- #
def play_game(difficulty):
    state = GameState(difficulty)
    highscore = load_highscore()

    clear()
    print("Get ready... Game starts in 2 seconds.")
    time.sleep(2)

    running = True
    message = ""

    # Terminal switched to cbreak mode ONCE for the whole game,
    # instead of on every single key poll (much cheaper, and Ctrl+C still works).
    with TerminalMode():
        while running:
            state.tick_shield()

            lane_idx, symbol = generate_row()
            state.row_history.insert(0, (lane_idx, symbol))

            reached_lane, reached_symbol = state.row_history.pop()
            message = ""
            if reached_symbol != EMPTY:
                running, message = handle_collision(state, reached_lane, reached_symbol)

            state.score += 1
            state.increase_difficulty()

            render(state, message)

            if not running:
                break

            # Poll for input without re-rendering on every keystroke (reduces flicker)
            start_time = time.time()
            moved = False
            while time.time() - start_time < state.speed:
                move = get_key_async()
                if move == "a" and state.car_lane > 0 and not moved:
                    state.car_lane -= 1
                    moved = True
                elif move == "d" and state.car_lane < LANES - 1 and not moved:
                    state.car_lane += 1
                    moved = True
                elif move == "q":
                    running = False
                    break
                time.sleep(0.02)

            if moved and running:
                render(state, message)

    clear()
    print_header("GAME OVER")
    print(f"Final Score: {state.score}".center(40))
    if state.score > highscore:
        print("🏆 New High Score!".center(40))
        save_highscore(state.score)
    else:
        print(f"High Score: {highscore}".center(40))

# --------------------------------------------------------------------------- #
# Menu system
# --------------------------------------------------------------------------- #
def choose_difficulty():
    clear()
    print_header("SELECT DIFFICULTY")
    print("1. Easy")
    print("2. Normal")
    print("3. Hard")
    choice = input("> ").strip()
    return {"1": "easy", "2": "normal", "3": "hard"}.get(choice, "normal")

def show_instructions():
    clear()
    print_header("HOW TO PLAY")
    print("""
 Control your car instantly using:
 [a] = Move Left      [d] = Move Right
 [q] = Quit Game

 * Avoid 'X' obstacles (Costs 1 Life).
 * Collect 'S' for a temporary shield.
 * Collect '$' for 5 bonus points.

 The game moves automatically.
 Speed increases as score grows!
    """)
    input("Press Enter to return to menu...")

def main_menu():
    while True:
        clear()
        print_header("CAR RACE")
        print("1. Play Game")
        print("2. Instructions")
        print("3. View High Score")
        print("4. Quit")
        choice = input("> ").strip()
        if choice == "1":
            difficulty = choose_difficulty()
            play_game(difficulty)
            input("\nPress Enter to continue...")
        elif choice == "2":
            show_instructions()
        elif choice == "3":
            clear()
            print_header("HIGH SCORE")
            print(f"Current High Score: {load_highscore()} points".center(40))
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            print("Thanks for playing!")
            break
        else:
            print("Invalid choice.")
            time.sleep(0.5)

if __name__ == "__main__":
    main_menu()
