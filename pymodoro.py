#!/usr/bin/env python3

# Authors: Alankar Misra, Claude.ai, ChatGPT

import time
import csv
import os
import sys
import select
import tty
import termios
import subprocess
import platform
import shutil
import threading
import json
from datetime import datetime

# === Config Management ===
CONFIG_FILE = 'pymodoro_config.json'

DEFAULT_CONFIG = {
    'WORK_MINUTES': 25,  # Traditional Pomodoro is 25 minutes
    'SHORT_BREAK_MINUTES': 5,
    'LONG_BREAK_MINUTES': 15,
    'SESSIONS_BEFORE_LONG_BREAK': 4,
    'STATE_FILE': '.last_pymodoro_title.txt',
    'LOG_FILE': 'pymodoro_log.csv',
    'MIN_SECONDS_TO_LOG': 60  # Minimum seconds for a session to be logged on exit
}

def load_config():
    """Load configuration from file, create with defaults if it doesn't exist."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all required keys exist, add defaults for missing ones
                for key, default_value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = default_value
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read config file ({e}). Using defaults.")
    
    # Create config file with defaults
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"Created config file: {CONFIG_FILE}")
    except IOError as e:
        print(f"Warning: Could not create config file ({e}). Using defaults.")
    
    return DEFAULT_CONFIG.copy()

CONFIG = load_config()

class PomodoroTimer:
    def __init__(self):
        self.paused = False
        self.pause_lock = threading.Lock()
        self.current_session = None  # Track current session for partial logging
        
    def get_last_title(self):
        """Get the last used session title."""
        try:
            if os.path.exists(CONFIG['STATE_FILE']):
                with open(CONFIG['STATE_FILE']) as f:
                    return f.read().strip()
        except IOError:
            print("Warning: Could not read last title file.")
        return ""

    def save_last_title(self, title):
        """Save the session title for next time."""
        try:
            with open(CONFIG['STATE_FILE'], "w") as f:
                f.write(title)
        except IOError:
            print("Warning: Could not save title file.")

    def log_session(self, title, minutes, session_type="work"):
        """Log completed session to CSV file."""
        try:
            file_exists = os.path.isfile(CONFIG['LOG_FILE'])
            with open(CONFIG['LOG_FILE'], mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists or os.stat(CONFIG['LOG_FILE']).st_size == 0:
                    writer.writerow(['title', 'minutes', 'datetime', 'type'])
                writer.writerow([title, minutes, datetime.now().isoformat(), session_type])
        except IOError:
            print("Warning: Could not write to log file.")

    def log_partial_session(self, title, elapsed_seconds, session_type="work"):
        """Log a partial session if it meets minimum duration requirements."""
        if elapsed_seconds >= CONFIG['MIN_SECONDS_TO_LOG']:
            minutes = elapsed_seconds / 60
            self.log_session(title, round(minutes, 2), f"partial_{session_type}")
            print(f"\n📝 Logged partial session: {round(minutes, 1)} minutes")

    def notify(self, title, message):
        """Send system notification with sound."""
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["osascript", "-e", 
                              f'display notification "{message}" with title "{title}"'], 
                              check=False)
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif system == "Linux":
                if shutil.which("notify-send"):
                    subprocess.run(["notify-send", title, message], check=False)
                # Try to play a sound
                for sound_cmd in ["paplay /usr/share/sounds/alsa/Front_Right.wav",
                                "aplay /usr/share/sounds/alsa/Front_Right.wav",
                                "play -q /usr/share/sounds/sound-icons/bell.wav"]:
                    if shutil.which(sound_cmd.split()[0]):
                        os.system(f"{sound_cmd} 2>/dev/null &")
                        break
                print(f"\n🔔 [{title}] {message}")
            elif system == "Windows":
                # Windows notification (requires Windows 10+)
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                except ImportError:
                    print(f"\n🔔 [{title}] {message}")
                # Windows beep
                import winsound
                winsound.Beep(800, 500)
            else:
                print(f"\n🔔 [{title}] {message}")
        except Exception:
            print(f"\n🔔 [{title}] {message}")

    def prompt_for_title(self):
        """Prompt user for session title with timeout."""
        last = self.get_last_title()
        print(f"Previous session title: '{last}'" if last else "No previous session title found.")
        print("Press Enter to change it, or wait 5 seconds to continue...")
        sys.stdout.flush()

        # Use select with timeout
        if sys.stdin in select.select([sys.stdin], [], [], 5)[0]:
            key = sys.stdin.read(1)
            if key == '\n':
                # Reset terminal for input
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
                try:
                    new_title = input("Enter new session title: ").strip()
                    return new_title or (last or "Pymodoro")
                finally:
                    tty.setcbreak(sys.stdin.fileno())
        
        return last or "Pymodoro"

    def handle_input(self):
        """Handle keyboard input in a separate thread."""
        while True:
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                try:
                    cmd = sys.stdin.read(1).lower()
                    if cmd == 'p':
                        with self.pause_lock:
                            self.paused = not self.paused
                except:
                    break

    def create_progress_bar(self, current, total, width=30):
        """Create a simple progress bar."""
        # Ensure progress never exceeds 100%
        progress = min(1.0, max(0.0, (total - current) / total))
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        percentage = int(100 * progress)
        return f'[{bar}] {percentage}%'

    def run_timer(self, minutes, label, session_type="work"):
        """Run a timer with pause/resume functionality."""
        total_seconds = int(minutes * 60)
        start_time = time.time()
        
        # Track current session for partial logging
        self.current_session = {
            'title': getattr(self, 'current_title', 'Pymodoro'),
            'start_time': start_time,
            'session_type': session_type,
            'total_seconds': total_seconds
        }
        
        # Start input handler thread
        input_thread = threading.Thread(target=self.handle_input, daemon=True)
        input_thread.start()
        
        print(f"⏱️  {label} — Press 'p' to pause/resume. Ctrl+C to quit.")
        
        try:
            while True:
                with self.pause_lock:
                    if not self.paused:
                        elapsed = time.time() - start_time
                        remaining = total_seconds - elapsed
                        
                        if remaining <= 0:
                            # Show 100% completion before breaking
                            print(f"\r⏳ 00:00 [{'█' * 30}] 100% {label}", 
                                  end='', flush=True)
                            break
                        
                        # Ensure we don't show negative time
                        remaining = max(0, remaining)
                        mins, secs = divmod(int(remaining), 60)
                        progress_bar = self.create_progress_bar(remaining, total_seconds)
                        print(f"\r⏳ {mins:02d}:{secs:02d} {progress_bar} {label}", 
                              end='', flush=True)
                    else:
                        print(f"\r⏸️  Paused - {label} (Press 'p' to resume)     ", 
                              end='', flush=True)
                        # Adjust start time to account for pause
                        pause_start = time.time()
                
                time.sleep(0.1)  # More responsive updates
                
                # If we were paused, adjust the start time
                if self.paused:
                    start_time += time.time() - pause_start

            print(f"\n✅ Finished: {label}")
            
            # Only send notification if it's not a 0-minute break session
            if minutes > 0 or session_type == "work":
                self.notify("Pymodoro", f"{label} complete!")
            
            # Clear current session since it completed normally
            self.current_session = None
            
        except KeyboardInterrupt:
            # Handle partial session logging on interrupt
            if self.current_session:
                elapsed_seconds = time.time() - self.current_session['start_time']
                self.log_partial_session(
                    self.current_session['title'], 
                    elapsed_seconds, 
                    self.current_session['session_type']
                )
            raise  # Re-raise to be handled by the main loop

    def run(self):
        """Main application loop."""
        self.old_settings = termios.tcgetattr(sys.stdin)
        session_count = 0

        try:
            tty.setcbreak(sys.stdin.fileno())
            
            # Get session title
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            title = self.prompt_for_title()
            self.save_last_title(title)
            self.current_title = title  # Store for partial logging
            tty.setcbreak(sys.stdin.fileno())

            print(f"\n🍅 Starting Pomodoro sessions for: {title}")
            print(f"Work: {CONFIG['WORK_MINUTES']}min, Short break: {CONFIG['SHORT_BREAK_MINUTES']}min, Long break: {CONFIG['LONG_BREAK_MINUTES']}min")
            print(f"Minimum session duration to log on exit: {CONFIG['MIN_SECONDS_TO_LOG']} seconds\n")

            while True:
                # Work session
                self.run_timer(CONFIG['WORK_MINUTES'], f"Work — {title}", "work")
                self.log_session(title, CONFIG['WORK_MINUTES'], "work")
                session_count += 1

                # Break session
                if session_count % CONFIG['SESSIONS_BEFORE_LONG_BREAK'] == 0:
                    self.run_timer(CONFIG['LONG_BREAK_MINUTES'], "Long Break", "long_break")
                    self.log_session(title, CONFIG['LONG_BREAK_MINUTES'], "long_break")
                    print(f"\n🎉 Completed {session_count} work sessions! Great job!\n")
                else:
                    if CONFIG['SHORT_BREAK_MINUTES'] > 0:
                        self.run_timer(CONFIG['SHORT_BREAK_MINUTES'], "Short Break", "short_break")
                        self.log_session(title, CONFIG['SHORT_BREAK_MINUTES'], "short_break")
                    else:
                        print("⏭️  Skipping short break (0 minutes configured)")

        except KeyboardInterrupt:
            print("\n👋 Exiting Pymodoro timer. Great work!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

def main():
    """Entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Pymodoro Timer")
        script_name = os.path.basename(sys.argv[0])
        print(f"Usage: {script_name}")
        print("   or: python pymodoro.py")
        print("   or: python3 pymodoro.py")
        print("\nDuring timer:")
        print("  p - pause/resume")
        print("  Ctrl+C - quit")
        print(f"\nConfig: {CONFIG['WORK_MINUTES']}min work, {CONFIG['SHORT_BREAK_MINUTES']}min short break, {CONFIG['LONG_BREAK_MINUTES']}min long break")
        print(f"Minimum duration to log partial sessions: {CONFIG['MIN_SECONDS_TO_LOG']} seconds")
        return
    
    timer = PomodoroTimer()
    timer.run()

if __name__ == "__main__":
    main()