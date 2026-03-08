# VTU Internship Diary – Auto-fill Bot 🤖

Automatically fills your daily internship diary entries on the [VTU internship portal](https://vtu.internyet.in) so you never have to do it manually.

> Built by VTU students, for VTU students. Works for **any company** registered in the portal.

---

## Features

- ✅ Automated login with session recovery (auto re-logs in if kicked out)
- ✅ Selects your internship automatically (works for any company)
- ✅ Navigates the calendar date picker
- ✅ Fills all form fields: Work Summary, Hours, Learnings, Blockers, Skills
- ✅ Configurable via `.env` and `config.json` — no code changes needed

---

## Prerequisites

- Python 3.10+
- Google Chrome
- [ChromeDriver](https://chromedriver.chromium.org/downloads) matching your Chrome version (or use `webdriver-manager`)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/vtu-diary-autofill.git
cd vtu-diary-autofill
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up your credentials

```bash
cp .env.example .env
```

Edit `.env` with your VTU portal login:

```
EMAIL=youremail@example.com
PASSWORD=yourpassword
```

> ⚠️ `.env` is gitignored and will **never** be pushed to GitHub.

### 4. Configure your internship

Edit `config.json`:

```json
{
    "internship_keyword": "",
    "wait_sec": 20,
    "sleep_page_load": 2.5,
    "sleep_dropdown": 1.5,
    "sleep_after_save": 4.0
}
```

| Field | Description |
|---|---|
| `internship_keyword` | Part of your company name (e.g. `"Infosys"`). Leave `""` to auto-pick the first (and only) registered internship. |
| `wait_sec` | Max seconds to wait for page elements |
| `sleep_page_load` | Seconds to wait after navigating to a new page |
| `sleep_dropdown` | Seconds to wait for skill dropdown to filter |
| `sleep_after_save` | Seconds to wait after clicking Save |

### 5. Prepare your diary entries

```bash
cp diary_entries.example.json diary_entries.json
```

Fill `diary_entries.json` with your entries. Each entry must follow this schema:

```json
[
    {
        "date": "01 Sep 2025",
        "work_summary": "Describe what you worked on today.",
        "hours": "8.0",
        "learnings": "What did you learn?",
        "blockers": "None.",
        "skills": "Python"
    }
]
```

#### Valid `skills` values

Check the portal's dropdown for the exact options. Common ones include:
- `Python`
- `Verification & Validations`
- `Business operations and Strategy`
- `UI/UX`
- `C++`
- `SQL`

> Only put **one skill per entry** — the bot selects the first matching option.

#### Date format

Dates must be `"DD Mon YYYY"` — e.g. `"07 Jul 2025"`, `"15 Oct 2025"`.

### 6. Run the bot

```bash
source env/bin/activate
python autofill_bot.py
```

The bot will open a Chrome window and fill entries one by one. You'll see live progress in the terminal.

---

## Troubleshooting

**Bot crashes on a specific entry**
The terminal will prompt you to fix the browser manually and press ENTER to skip that entry and continue.

**"Session expired" mid-run**
The bot automatically detects this and re-logs in. No action needed.

**ChromeDriver version mismatch**
Install [`webdriver-manager`](https://pypi.org/project/webdriver-manager/) and change the driver line in `autofill_bot.py`:
```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
```

**Bot is too fast / elements not loading**
Increase `sleep_page_load` and `sleep_after_save` in `config.json`.

---

## Project structure

```
vtu-diary-autofill/
├── autofill_bot.py             # Main bot script
├── config.json                 # Your settings (committed)
├── diary_entries.json          # Your diary data (gitignored)
├── diary_entries.example.json  # Schema template
├── .env                        # Your credentials (gitignored)
├── .env.example                # Credential template
├── requirements.txt
└── README.md
```

---

## Contributing

PRs and issues are welcome! If the portal's HTML changes and the bot breaks, open an issue with a screenshot of the failing element.

---

## License

MIT
