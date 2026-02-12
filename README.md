# AI Course Tracker

Lightweight Python tool that periodically scrapes specified learning platforms for 100%‑off / 0‑cost courses and sends Telegram notifications for newly discovered courses only.

**Key features**
- Checks the configured source URLs every 2 hours (scheduler).
- Sends a single Telegram message per new free course found.
- Sends one message "No new courses found." when nothing new appears.
- Persists already-sent course links in `sent_courses.json` to avoid duplicates.

Requirements
------------
- Python 3.8+
- Packages: `requests`, `beautifulsoup4`, `schedule`

Install dependencies
--------------------
```powershell
pip install requests beautifulsoup4 schedule
```

Configuration
-------------
- Do NOT modify `config.py` or `notifier.py` unless you know what you are doing.
- `config.py` contains `BOT_TOKEN` and `CHAT_ID` used by the existing `send_telegram_message()` in `notifier.py`.

Quick run (one-shot check)
--------------------------
Run a single check without entering the continuous scheduler:
```powershell
python -c "from main import check_and_notify; check_and_notify()"
```

Run continuously
----------------
Run the full application (checks once on start, then every 2 hours):
```powershell
python main.py
```

How it detects free courses
---------------------------
- Scrapes the provided platform pages with `requests` + `BeautifulSoup`.
- Uses listing DOM text and stronger page-level heuristics (looks for JSON/script patterns such as `amount:0`, `"isPaid": false`, `100% off`, `$0`) to confirm a course is 0 cost before notifying.

Persistence and duplicate prevention
-----------------------------------
- Sent course links are stored in `sent_courses.json`.
- The app will never resend links that are already present in that file.

Files
-----
- `main.py`: orchestrates scraping, notifications, and scheduling.
- `course_scraper.py`: scraping + heuristics to confirm 0‑cost courses.
- `storage.py`: JSON persistence for sent links.
- `scheduler.py`: helper to run the scheduler in background (used by `main.py`).
- `notifier.py`: existing file that exposes `send_telegram_message()` — used for Telegram sends.
- `config.py`: existing configuration file (contains `BOT_TOKEN`, `CHAT_ID`, `KEYWORDS`).

Troubleshooting
---------------
- If no messages are delivered, verify `BOT_TOKEN` and `CHAT_ID` in `config.py`.
- Network errors are logged to the console; the scraper continues on error.
- To reset notifications for testing, delete or edit `sent_courses.json` (it is safe to edit while the app is stopped).

Notes
-----
- The scraper avoids headless browser tooling — it is implemented using `requests` and `BeautifulSoup` only.
- The detection is heuristic-based: some platform changes may require updates to `course_scraper.py`.
