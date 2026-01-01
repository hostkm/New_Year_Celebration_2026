import time
import os
import random
import shutil
import threading

try:
    import winsound
except Exception:
    winsound = None

# ================= TERMINAL =================

os.system("")  # enable ANSI on Windows

def clear():
    print("\033[2J\033[H", end="")

def hide_cursor():
    print("\033[?25l", end="")

def show_cursor():
    print("\033[?25h", end="")

# ================= COLORS =================

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"

# ================= ASCII DIGITS =================

DIGITS = {
    "0": [" █████ ", "██   ██", "██   ██", "██   ██", " █████ "],
    "1": ["   ██  ", " ████  ", "   ██  ", "   ██  ", " ██████"],
    "2": [" █████ ", "     ██", " █████ ", "██     ", "███████"],
    "3": ["██████ ", "     ██", " █████ ", "     ██", "██████ "],
    "4": ["██   ██", "██   ██", "███████", "     ██", "     ██"],
    "5": ["███████", "██     ", "██████ ", "     ██", "██████ "],
    "6": [" █████ ", "██     ", "██████ ", "██   ██", " █████ "]
}

# ================= UTIL =================

def term_size():
    size = shutil.get_terminal_size((80, 24))
    return size.columns, size.lines

# ================= DRAW =================

def draw_year(state, shift):
    """
    state:
      "2025"      -> static 2025
      "TRANSITION"-> animate 5 -> 6
      "2026"      -> static 2026

        shift (TRANSITION): 0..5 progress steps
    """
    w, h = term_size()
    clear()
    print("\n" * (h // 2 - 6), end="")

    for row in range(5):
        line = ""

        # static 2 0 2
        for d in ["2", "0", "2"]:
            line += DIGITS[d][row] + "  "

        if state == "2025":
            line += DIGITS["5"][row]

        elif state == "TRANSITION":
            # 5 goes down while 6 comes up from the bottom (overlapped in the same slot)
            slot = list("       ")

            r5 = row - shift
            if 0 <= r5 < 5:
                slot = list(DIGITS["5"][r5])

            r6 = row + shift - 5
            if 0 <= r6 < 5:
                overlay = DIGITS["6"][r6]
                for i, ch in enumerate(overlay):
                    if ch != " ":
                        slot[i] = ch

            line += "".join(slot)

        elif state == "2026":
            line += DIGITS["6"][row]

        print(BOLD + line.center(w) + RESET)

def draw_clock(h, m, s):
    w, _ = term_size()
    print()
    print(CYAN + BOLD + f"{h:02d}:{m:02d}:{s:02d}".center(w) + RESET)

def draw_message():
    w, _ = term_size()
    print()
    print(GREEN + BOLD + "🎉 HAPPY NEW YEAR 2026 🎉".center(w) + RESET)

def draw_stars():
    w, h = term_size()
    for _ in range(20):
        # avoid the last column/row to prevent line-wrapping/scrolling
        x = random.randint(1, max(1, w - 2))
        y = random.randint(1, max(1, h - 1))
        print(f"\033[{y};{x}H✨", end="")
    print(f"\033[{h};1H", end="", flush=True)

def draw_confetti_burst():
    w, h = term_size()
    symbols = ["🎉", "✨", "🎆", "🎇", "🥳", "⭐"]
    count = min(120, max(30, (w * h) // 200))
    for _ in range(count):
        # avoid the last column/row to prevent emoji wrapping/scrolling
        x = random.randint(1, max(1, w - 2))
        y = random.randint(1, max(1, h - 1))
        sym = random.choice(symbols)
        print(f"\033[{y};{x}H{sym}", end="")
    # put cursor back at bottom so the frame stays stable
    print(f"\033[{h};1H", end="", flush=True)

# ================= SOUND =================

def _beep(freq=880, dur=120):
    if winsound is not None:
        try:
            winsound.Beep(int(freq), int(dur))
            return
        except Exception:
            pass
    # fallback: terminal bell (may be disabled in some terminals)
    print("\a", end="", flush=True)

def tick_beep_async():
    threading.Thread(target=_beep, args=(880, 120), daemon=True).start()

def celebration_sound_async():
    def _celebrate():
        # small "celebration" melody using beeps
        for f, d in [(880, 120), (1175, 120), (1568, 160), (1175, 120), (1568, 220)]:
            _beep(f, d)
            time.sleep(0.03)

        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    threading.Thread(target=_celebrate, daemon=True).start()

# ================= MAIN =================

def main():
    hide_cursor()
    try:
        start = time.time()

        did_midnight_sound = False

        # simulated start time = 23:57:00
        base = 23 * 3600 + 57 * 60

        while True:
            elapsed = int(time.time() - start)
            t = base + elapsed

            h = (t // 3600) % 24
            m = (t % 3600) // 60
            s = t % 60

            # stop at 00:03:00
            if h == 0 and m == 3 and s == 0:
                break

            # ----- STATE DECISION -----
            if h == 23 and m < 59:
                state = "2025"
                shift = 0

            elif h == 23 and m == 59:
                # shift: 0..5, and at 23:59:59 the shift reaches 5
                state = "TRANSITION"
                shift = (s + 1) * 5 // 60

            else:
                # At 00:00:00 and beyond: 2026 fully shown, 2025 fully gone
                state = "2026"
                shift = 0
            # --------------------------

            # ----- SOUND EVENTS -----
            # last 10 seconds countdown beeps
            if h == 23 and m == 59 and 50 <= s <= 59:
                tick_beep_async()

            # celebration sound exactly at midnight (once)
            if (not did_midnight_sound) and h == 0 and m == 0 and s == 0:
                did_midnight_sound = True
                celebration_sound_async()
            # ------------------------

            draw_year(state, shift)
            draw_clock(h, m, s)

            if h == 0:
                draw_message()
                draw_stars()

                if m == 0 and s == 0:
                    draw_confetti_burst()

            time.sleep(1)

    finally:
        show_cursor()
        clear()

# ================= RUN =================

if __name__ == "__main__":
    main()
