# 📓 VTU Internship Diary – Auto-fill Bot

> Hate filling diary entries by hand? This bot logs into the [VTU internship portal](https://vtu.internyet.in), picks your date, selects your internship, fills every field, and hits Save — automatically, for every entry in your list.

---

## What it does

Each diary entry on the portal requires you to:
1. Log in
2. Go to **Create Entry**
3. Select your internship from a dropdown
4. Pick the date from a calendar
5. Click **Continue**
6. Fill in Work Summary, Hours, Learnings, Blockers, and Skills
7. Hit **Save**
8. Repeat for every single day of your internship 😮‍💨

**This bot does all of that for you**, for as many entries as you put in `diary_entries.json`.

---

## Quick start (5 steps)

### Step 1 — Clone & install

```bash
git clone https://github.com/SrivathsavS/vtu-diary-autofill.git
cd vtu-diary-autofill

python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

> **Requires:** Python 3.10+, Google Chrome, and [ChromeDriver](https://chromedriver.chromium.org/downloads) matching your Chrome version.

---

### Step 2 — Add your credentials

```bash
cp .env.example .env    

# windows might use copy instead of cp
```

Open `.env` and fill in your VTU portal login:

```
EMAIL=youremail@example.com
PASSWORD=yourpassword
```

> 🔒 `.env` is listed in `.gitignore` — it will **never** be committed or pushed.

---

### Step 3 — Set your company name (optional)

Open `config.json`:

```json
{
    "internship_keyword": "",
    "wait_sec": 20,
    "sleep_page_load": 2.5,
    "sleep_dropdown": 1.5,
    "sleep_after_save": 4.0
}
```

- **`internship_keyword`** — Part of your company's name (e.g. `"Infosys"`). The bot will look for this in the dropdown and select it. Leave it as `""` to automatically pick the first (and only) internship registered under your account — this works for most students.
- **`sleep_page_load`** — Increase this (e.g. to `3.5`) if the bot is clicking before the page finishes loading.
- **`sleep_after_save`** — Time to wait after saving each entry before moving to the next.

---

### Step 4 — Prepare your diary entries

```bash
cp diary_entries.example.json diary_entries.json
```

Open `diary_entries.json` and fill it with your entries. Each entry looks like this:

```json
[
    {
        "date": "01 Sep 2025",
        "work_summary": "What did you work on today?",
        "hours": "8.0",
        "learnings": "What did you learn?",
        "blockers": "None.",
        "skills": "Python"
    },
    {
        "date": "02 Sep 2025",
        "work_summary": "Continue filling entries...",
        "hours": "8.0",
        "learnings": "More learnings.",
        "blockers": "None.",
        "skills": "Verification & Validations"
    }
]
```

Use any ai chat bot to create one for your specifiations.

#### Field reference

| Field | Format | Example |
|---|---|---|
| `date` | `"DD Mon YYYY"` | `"07 Jul 2025"` |
| `work_summary` | Any text | `"Wrote unit tests for the payment module."` |
| `hours` | Number as string | `"8.0"` |
| `learnings` | Any text | `"Learned how pytest fixtures work."` |
| `blockers` | Any text, or `"None."` | `"None."` |
| `skills` | Must match a portal option exactly | See list below |

#### Available skills (must match exactly)

- `Python`
- `Verification & Validations`
- `Business operations and Strategy`
- `UI/UX`
- `C++`
- `SQL`

> Only one skill per entry. Check the portal's Skills dropdown for the full list available to you.

---

### Step 5 — Run it

```bash
source env/bin/activate
python autofill_bot.py
```

A Chrome window will open and the bot will start filling entries. Watch the terminal for live progress:

```
────────────────────────────────────────────────────────────
  VTU Internship Diary – Auto-fill Bot
────────────────────────────────────────────────────────────
  Account  : youremail@example.com
  Internship keyword: first available (auto)
  Entries to process: 45
────────────────────────────────────────────────────────────
Logging in …
✔  Logged in!

============================================================
  Entry 1/45  |  Date: 01 Sep 2025
============================================================
▸ Step 1: Opening create-entry page …
▸ Step 2: Selecting internship …
▸ Step 3: Picking date 01 Sep 2025 …
...
✔  Entry 1/45 saved!
```

---

## When something goes wrong

**Bot crashes on one entry**
The terminal will print the error and prompt you to fix it manually in the browser, then press ENTER. The bot will skip that entry and continue with the rest.

**"Session expired — re-logging in"**
The bot detected it got logged out and will automatically log back in. Nothing you need to do.

**Elements not loading / bot clicking too fast**
Increase `sleep_page_load` and `sleep_after_save` in `config.json` (e.g. try `3.5` and `5.0`).

**ChromeDriver version mismatch error**
Install `webdriver-manager` to handle this automatically:
```bash
pip install webdriver-manager
```
Then change the driver line in `autofill_bot.py`:
```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

---

## File structure

```
vtu-diary-autofill/
├── autofill_bot.py              # The bot
├── config.json                  # Your settings (safe to commit)
├── diary_entries.json           # Your diary data  ← gitignored
├── diary_entries.example.json   # Schema template
├── .env                         # Your credentials ← gitignored
├── .env.example                 # Credential template
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Contributing

Found a bug or the portal's HTML changed and broke something? Open an issue — PRs are welcome.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

Copyright 2026 Srivathsav S
