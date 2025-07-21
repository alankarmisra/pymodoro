#!/usr/bin/env python3

# Author: ChatGPT

import time
import csv
import os
import sys
import select
import tty
import termios
import subprocess
import platform
from datetime import datetime

# === Config ===
WORK_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
SESSIONS_BEFORE_LONG_BREAK = 4

STATE_FILE = ".last_pymodoro_title.txt"
LOG_FILE = "pymodoro_log.csv"

def get_last_title():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return f.read().strip()
    return ""

def save_last_title(title):
    with open(STATE_FILE, "w") as f:
        f.write(title)

def log_session(title, minutes, session_type="work"):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists or os.stat(LOG_FILE).st_size == 0:
            writer.writerow(['title', 'minutes', 'datetime', 'type'])
        writer.writerow([title, minutes, datetime.now().isoformat(), session_type])

def notify(title, message):
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])
        os.system("afplay /System/Library/Sounds/Glass.aiff")
    elif system == "Linux":
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message])
        else:
            print(f"[{title}] {message}")
    elif system == "Windows":
        print(f"[{title}] {message}")
    else:
        print(f"[{title}] {message}")

def prompt_for_title():
    last = get_last_title()
    print(f"Previous session title: '{last}'" if last else "No previous session title found.")
    print("Press Enter to change it. You have 5 seconds…")
    sys.stdout.flush()

    rlist, _, _ = select.select([sys.stdin], [], [], 5)

    if rlist:
        key = sys.stdin.read(1)
        if key == '\n':
            new_title = input("Enter new session title: ").strip()
            return new_title or (last or "Pymodoro")
    
    return last or "Pymodoro"

def run_timer(minutes, label):
    total_seconds = int(minutes * 60)
    remaining = total_seconds
    paused = False
    start_time = time.time()

    print(f"⏱️ {label} — Press 'p' to pause/resume. Ctrl+C to quit.")

    while remaining > 0:
        if not paused:
            mins, secs = divmod(int(remaining), 60)
            print(f"\r⏳ {mins:02d}:{secs:02d} - {label} ", end='', flush=True)
            time.sleep(1)
            remaining = total_seconds - (time.time() - start_time)
        else:
            print(f"\r⏸ Paused - {label}         ", end='', flush=True)
            time.sleep(0.2)

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.read(1)
            if cmd.lower() == 'p':
                paused = not paused
                if not paused:
                    start_time = time.time() - (total_seconds - remaining)

    print(f"\n✅ Finished: {label}")
    notify("Pymodoro", f"{label} complete!")

if __name__ == "__main__":
    import shutil
    old_settings = termios.tcgetattr(sys.stdin)
    session_count = 0

    try:
        tty.setcbreak(sys.stdin.fileno())

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        title = prompt_for_title()
        save_last_title(title)
        tty.setcbreak(sys.stdin.fileno())

        while True:
            run_timer(WORK_MINUTES, f"Work — {title}")
            log_session(title, WORK_MINUTES, "work")
            session_count += 1

            if session_count % SESSIONS_BEFORE_LONG_BREAK == 0:
                run_timer(LONG_BREAK_MINUTES, "Long Break")
                log_session(title, LONG_BREAK_MINUTES, "long_break")
            else:
                run_timer(SHORT_BREAK_MINUTES, "Short Break")
                log_session(title, SHORT_BREAK_MINUTES, "short_break")

    except KeyboardInterrupt:
        print("\n👋 Exiting Pymodoro timer.")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        