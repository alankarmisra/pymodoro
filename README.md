# 🕒 Terminal Pomodoro Timer (Mac-friendly)

A minimalist, keyboard-driven Pomodoro timer built in Python for your terminal.
Designed for focused work with zero distractions, native macOS notifications, and local CSV logging.

---

## ✅ Features

* ⏱️ 25-minute default work sessions (configurable)
* 📝 Session title prompt (auto-uses previous unless changed)
* ⏳ Smart title input timeout (auto-starts unless Enter is pressed)
* ⌨️ Keyboard controls: `p` to pause/resume, `Ctrl+C` to quit
* 🗂️ CSV logging of session `title`, `minutes`, and `timestamp`
* 🔔 macOS notification and system sound on session completion
* ♻️ Automatically repeats work/break cycles

---

## 📸 Screenshot

(Note: Work session time reduced for screenshots)

<img width="794" height="422" alt="Screenshot 2025-07-21 at 7 17 33 PM" src="https://github.com/user-attachments/assets/739124ae-1624-4c3f-93ae-7ee31fcd52a9" />

<img width="838" height="257" alt="Screenshot 2025-07-21 at 8 10 36 PM" src="https://github.com/user-attachments/assets/a9cbf2c2-aef6-416b-a3e7-3a817f2921f3" />


---

## 🔧 Requirements

* Python 3
* macOS for native notifications (`osascript`) and audio (`afplay`)

> On Linux/Windows, the script will gracefully fall back to printing alerts to the terminal.

---

## ⚙️ Configuration

Modify these variables at the top of the script to change default durations:

```python
WORK_MINUTES = 25
BREAK_MINUTES = 5
```

---

## 📂 Log Output

Session data is saved to a local CSV file (`pymodoro_log.csv`) with the format:

```
title,minutes,datetime
Writing project notes,20,2025-07-21T17:12:34.123456
```

---

## 🧪 How It Works

1. On start, the script shows your last session title.
2. Press `Enter` within 5 seconds to change it.
3. Otherwise, the timer starts with the existing title.
4. When the timer completes, you get:

   * A native macOS notification
   * A "ding" sound
   * An automatic break (if configured)
   * Continuous work/break loops until stopped

---

## 🚀 Run It

Make it executable:

```bash
chmod +x pymodoro.py
```

Then run:

```bash
./pymodoro.py
```

---

## 📦 Future Ideas

* Menu bar integration via [xbar](https://xbarapp.com/)
* Desktop notifications for Linux and Windows
* Config file or command-line args for durations and logging

---

## 📄 License

MIT — feel free to use, modify, and share.

---

## ✨ Credits

Built with ☕️, ⌨️, and ✨ by Alankar Misra
Powered by [ChatGPT](https://openai.com/chatgpt)
