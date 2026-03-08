"""
VTU Internship Diary – Auto-fill Bot
=====================================
Automatically fills daily internship diary entries on the VTU portal
(https://vtu.internyet.in) using Selenium.

Configuration:
  .env              → EMAIL, PASSWORD  (never commit this file)
  config.json       → internship_keyword, wait times, etc.
  diary_entries.json → your diary data (see diary_entries.example.json)

Usage:
  pip install -r requirements.txt
  cp .env.example .env          # fill in your credentials
  cp diary_entries.example.json diary_entries.json   # fill in your entries
  python autofill_bot.py
"""

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# ── Load credentials from .env ────────────────────────────────────────────────
load_dotenv()
EMAIL    = os.getenv("EMAIL", "").strip()
PASSWORD = os.getenv("PASSWORD", "").strip()

if not EMAIL or not PASSWORD:
    raise SystemExit(
        "\n[!] EMAIL or PASSWORD not set.\n"
        "    Copy .env.example → .env and fill in your credentials."
    )

# ── Load config from config.json ──────────────────────────────────────────────
with open("config.json", "r") as _f:
    _cfg = json.load(_f)

# Internship keyword (optional): if non-empty the bot looks for a dropdown
# option whose text CONTAINS this string; falls back to the first option.
# Leave as "" to always pick the first (and only) internship in your portal.
INTERNSHIP_KEYWORD = _cfg.get("internship_keyword", "").strip()

WAIT_SEC         = _cfg.get("wait_sec",          20)
SLEEP_PAGE_LOAD  = _cfg.get("sleep_page_load",  2.5)
SLEEP_DROPDOWN   = _cfg.get("sleep_dropdown",   1.5)
SLEEP_AFTER_SAVE = _cfg.get("sleep_after_save", 4.0)

# ── URLs (VTU portal) ─────────────────────────────────────────────────────────
LOGIN_URL  = "https://vtu.internyet.in/sign-in"
LIST_URL   = "https://vtu.internyet.in/dashboard/student/diary-entries"
CREATE_URL = "https://vtu.internyet.in/dashboard/student/student-diary"

# ── Calendar month names ──────────────────────────────────────────────────────
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Load diary entries ────────────────────────────────────────────────────────
if not os.path.exists("diary_entries.json"):
    raise SystemExit(
        "\n[!] diary_entries.json not found.\n"
        "    Copy diary_entries.example.json → diary_entries.json and fill it in."
    )
with open("diary_entries.json", "r") as _f:
    entries = json.load(_f)

# ── Start browser ─────────────────────────────────────────────────────────────
driver = webdriver.Chrome()
wait   = WebDriverWait(driver, WAIT_SEC)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def scroll_click(el):
    """Scroll element into view, then click it."""
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.25)
    el.click()


def find_first(xpaths, use_wait=True):
    """Try multiple XPath locators and return the first element found."""
    for xp in xpaths:
        try:
            if use_wait:
                return wait.until(EC.visibility_of_element_located((By.XPATH, xp)))
            else:
                return driver.find_element(By.XPATH, xp)
        except Exception:
            pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# CALENDAR HELPER
# Days:  <button data-day="DD/MM/YYYY"> inside <td data-day="YYYY-MM-DD">
# Month: <select aria-label="Choose the Month">  (opacity-0, interactive)
# Year:  <select aria-label="Choose the Year">   (opacity-0, interactive)
# ─────────────────────────────────────────────────────────────────────────────

def pick_date_in_calendar(date_str):
    """
    Open the date-picker popover, navigate to the correct month/year via the
    hidden <select> elements, then click the target day.

    date_str format: "07 Jul 2025"
    """
    dt               = datetime.strptime(date_str, "%d %b %Y")
    target_day       = dt.day
    target_year      = dt.year
    target_month_idx = dt.month - 1          # 0-based (Jan = 0)
    target_data_day  = dt.strftime("%Y-%m-%d")   # used on <td>
    target_btn_day   = dt.strftime("%d/%m/%Y")   # used on <button>

    # 1. Open the calendar popover
    date_trigger = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//button[@data-slot='popover-trigger']"
        " | //button[.//span[normalize-space()='Pick a Date']]"
        " | //button[contains(@class,'text-gray-500') and .//svg[contains(@class,'lucide-calendar')]]"
    )))
    driver.execute_script("arguments[0].click();", date_trigger)
    time.sleep(0.8)

    # 2. Set year
    year_sel_el = wait.until(EC.presence_of_element_located((
        By.XPATH, "//select[@aria-label='Choose the Year']"
    )))
    Select(year_sel_el).select_by_visible_text(str(target_year))
    time.sleep(0.4)

    # 3. Set month
    month_sel_el = driver.find_element(By.XPATH, "//select[@aria-label='Choose the Month']")
    Select(month_sel_el).select_by_index(target_month_idx)
    time.sleep(0.4)

    # 4. Click the day
    day_xpaths = [
        f"//button[@data-day='{target_btn_day}']",
        f"//td[@data-day='{target_data_day}']//button",
        f"//button[contains(@class,'rdp-day') and normalize-space()='{target_day}']",
        f"//td[@role='gridcell' and not(contains(@class,'outside'))]//button[normalize-space()='{target_day}']",
    ]
    day_el = None
    for xp in day_xpaths:
        try:
            day_el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
            break
        except Exception:
            pass
    if day_el is None:
        raise RuntimeError(
            f"Could not click day {target_day} for {dt.strftime('%b %Y')} "
            f"(tried data-day={target_btn_day})"
        )
    driver.execute_script("arguments[0].click();", day_el)
    time.sleep(0.4)


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def do_login():
    """Navigate to the sign-in page and log in with credentials from .env."""
    driver.get(LOGIN_URL)
    time.sleep(1.5)
    email_el = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH,
        "//input[@placeholder='Enter your email address']"
        " | //input[@type='email']"
        " | //input[@name='email']"
    )))
    email_el.clear()
    email_el.send_keys(EMAIL)

    pass_el = driver.find_element(By.XPATH,
        "//input[@placeholder='Enter your password']"
        " | //input[@type='password']"
        " | //input[@name='password']"
    )
    pass_el.clear()
    pass_el.send_keys(PASSWORD)

    submit_el = driver.find_element(By.XPATH,
        "//button[normalize-space()='Sign In']"
        " | //button[@type='submit']"
        " | //input[@type='submit']"
    )
    submit_el.click()
    WebDriverWait(driver, 30).until(EC.url_contains("/dashboard"))


def ensure_logged_in():
    """
    Check if the session expired (redirected to sign-in page) and re-login
    automatically. Called at the start of every entry iteration.
    """
    if "sign-in" in driver.current_url or "login" in driver.current_url:
        print("\n[!] Session expired — re-logging in …")
        try:
            do_login()
            print("✔  Re-logged in!")
        except Exception as e:
            print(f"[!] Re-login failed: {e}")
            print("Please log in manually in the browser, then press ENTER.")
            input("➜  Press ENTER when logged in …\n")


# ─────────────────────────────────────────────────────────────────────────────
# INTERNSHIP SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def select_internship():
    """
    Open the internship dropdown and select the correct option.

    Strategy:
      1. If INTERNSHIP_KEYWORD is set in config.json, look for an option whose
         text contains that keyword.
      2. Fall back to the FIRST available option (works for everyone who only
         has one internship registered in the portal).
    """
    intern_trigger = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "//button[@id='internship_id']"
        " | //button[@role='combobox']"
        " | //button[.//span[@data-slot='select-value']]"
    )))
    driver.execute_script("arguments[0].click();", intern_trigger)
    time.sleep(0.8)

    # Build the XPath: keyword-specific first, then first-option fallback
    if INTERNSHIP_KEYWORD:
        option_xpath = (
            f"//*[@role='option' and contains(normalize-space(),'{INTERNSHIP_KEYWORD}')]"
            f" | //*[@data-slot='select-item' and contains(normalize-space(),'{INTERNSHIP_KEYWORD}')]"
            # fallback to first option if keyword not found
            " | (//*[@role='option'])[1]"
            " | (//*[@data-slot='select-item'])[1]"
        )
    else:
        option_xpath = (
            "(//*[@role='option'])[1]"
            " | (//*[@data-slot='select-item'])[1]"
        )

    intern_option = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
    driver.execute_script("arguments[0].click();", intern_option)
    time.sleep(0.5)


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP BANNER
# ─────────────────────────────────────────────────────────────────────────────

print("─" * 60)
print("  VTU Internship Diary – Auto-fill Bot")
print("─" * 60)
print(f"  Account  : {EMAIL}")
kw_display = f'"{INTERNSHIP_KEYWORD}"' if INTERNSHIP_KEYWORD else "first available (auto)"
print(f"  Internship keyword: {kw_display}")
print(f"  Entries to process: {len(entries)}")
print("─" * 60)

print("Logging in …")
try:
    do_login()
    print("✔  Logged in!\n")
except Exception as e:
    print(f"\n[!] Auto-login failed: {type(e).__name__}: {e}")
    print("Please log in manually in the browser, then press ENTER.")
    input("➜  Press ENTER when logged in …\n")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

total = len(entries)
for idx, entry in enumerate(entries, start=1):
    print(f"\n{'='*60}")
    print(f"  Entry {idx}/{total}  |  Date: {entry['date']}")
    print(f"{'='*60}")

    try:
        # ── Step 1: Navigate to create page ───────────────────────────────
        print("▸ Step 1: Opening create-entry page …")
        driver.get(CREATE_URL)
        time.sleep(SLEEP_PAGE_LOAD)

        # ── Session check: auto re-login if session expired ───────────────
        ensure_logged_in()
        if CREATE_URL not in driver.current_url:
            driver.get(CREATE_URL)
            time.sleep(SLEEP_PAGE_LOAD)

        # ── Step 2: Select internship ──────────────────────────────────────
        print("▸ Step 2: Selecting internship …")
        select_internship()

        # ── Step 3: Pick date ──────────────────────────────────────────────
        print(f"▸ Step 3: Picking date {entry['date']} …")
        pick_date_in_calendar(entry["date"])

        # ── Step 4: Continue ───────────────────────────────────────────────
        print("▸ Step 4: Clicking Continue …")
        continue_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//button[normalize-space()='Continue']"
            " | //button[contains(normalize-space(),'Continue')]"
        )))
        driver.execute_script("arguments[0].click();", continue_btn)
        time.sleep(SLEEP_PAGE_LOAD)

        # ── Step 5: Work Summary ───────────────────────────────────────────
        print("▸ Step 5: Work Summary …")
        ws = find_first([
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'DESCRIBE')]",
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'SUMMARY')]",
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BRIEFLY')]",
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'WORK')]",
            "(//textarea)[1]",
        ])
        if ws is None:
            raise RuntimeError("Work Summary textarea not found.")
        scroll_click(ws)
        ws.clear()
        ws.send_keys(entry["work_summary"])

        # ── Step 6: Hours ──────────────────────────────────────────────────
        print("▸ Step 6: Hours …")
        hrs = find_first([
            "//input[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'E.G')]",
            "//input[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'HOUR')]",
            "//input[@type='number']",
        ], use_wait=False)
        if hrs is None:
            raise RuntimeError("Hours input not found.")
        scroll_click(hrs)
        hrs.clear()
        hrs.send_keys(entry["hours"])

        # ── Step 7: Learnings ──────────────────────────────────────────────
        print("▸ Step 7: Learnings …")
        learn = find_first([
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'LEARN')]",
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'SHIP')]",
            "(//textarea)[2]",
        ], use_wait=False)
        if learn is None:
            raise RuntimeError("Learnings textarea not found.")
        scroll_click(learn)
        learn.clear()
        learn.send_keys(entry["learnings"])

        # ── Step 8: Blockers ───────────────────────────────────────────────
        print("▸ Step 8: Blockers …")
        block = find_first([
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BLOCK')]",
            "//textarea[contains(translate(@placeholder,"
            "'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'SLOW')]",
            "(//textarea)[3]",
        ], use_wait=False)
        if block is None:
            raise RuntimeError("Blockers textarea not found.")
        scroll_click(block)
        block.clear()
        block.send_keys(entry["blockers"])

        # ── Step 9: Skills (React Select component) ────────────────────────
        # HTML: <input id="react-select-2-input" class="react-select__input" role="combobox">
        print("▸ Step 9: Skills …")
        skills_el = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//input[@id='react-select-2-input']"
            " | //input[contains(@class,'react-select__input')]"
            " | //input[@role='combobox' and @aria-autocomplete='list']"
        )))
        driver.execute_script("arguments[0].click();", skills_el)
        skills_el.send_keys(entry["skills"])
        time.sleep(SLEEP_DROPDOWN)

        print("▸ Step 10: Selecting skill from dropdown …")
        skill_option = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            f"//*[@role='option' and contains(normalize-space(),'{entry['skills']}')]"
            f" | //div[contains(@class,'react-select__option') and contains(normalize-space(),'{entry['skills']}')]"
            " | (//*[@role='listbox']//*[@role='option'])[1]"
            " | (//div[contains(@class,'react-select__option')])[1]"
        )))
        driver.execute_script("arguments[0].click();", skill_option)
        time.sleep(0.4)

        # ── Step 11: Save ──────────────────────────────────────────────────
        print("▸ Step 11: Saving …")
        save_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//button[normalize-space()='Save']"
            " | //button[contains(normalize-space(),'Save')]"
            " | //button[@type='submit']"
        )))
        driver.execute_script("arguments[0].click();", save_btn)

        print(f"✔  Entry {idx}/{total} saved!")
        time.sleep(SLEEP_AFTER_SAVE)

        # Navigate away so the next iteration starts clean
        if CREATE_URL in driver.current_url:
            driver.get(LIST_URL)
            time.sleep(1.5)

    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"  [CRASH]  Entry {idx}/{total}  |  {entry['date']}")
        print(f"  Error   : {type(e).__name__}: {e}")
        print(f"{'!'*60}")
        print("Fix the browser manually, navigate back to the list page,")
        print("then press ENTER to SKIP this entry and continue.")
        input("➜  Press ENTER …\n")

print("\n" + "="*60)
print("  All entries processed. Done!")
print("="*60)
driver.quit()