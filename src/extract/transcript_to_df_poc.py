import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

API_URL = "https://avatar.fandom.com/api.php"
PAGE = "Transcript:The_Boy_in_the_Iceberg"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# "Transcript:The_Boy_in_the_Iceberg" -> "The Boy in the Iceberg"
EPISODE_TITLE = PAGE.split(":", 1)[-1].replace("_", " ")

BOOK_NUMBERS = {"one": 1, "two": 2, "three": 3, "1": 1, "2": 2, "3": 3}


def fetch_page(page: str) -> dict:
    """Fetch rendered HTML + categories for a wiki page via the API."""
    params = {
        "action": "parse",
        "page": page,
        "prop": "text|categories",
        "format": "json",
        "formatversion": 2,
    }
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "parse" not in data:
        raise RuntimeError(f"API did not return the page: {data}")
    return data["parse"]


LIST_PAGE = "List_of_Avatar:_The_Last_Airbender_episodes"


def norm(s: str) -> str:
    """Lowercase, drop quotes/punctuation so titles compare cleanly."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def lookup_in_episode_list(list_soup: BeautifulSoup, title: str):
    """
    Walk the wiki's episode list in document order. Headings like
    'Book One: Water' set the current season; table rows have the columns
    Title | Original air date | Chapter # | Episode #.
    Returns (season, chapter_in_season, overall_episode) or None.
    """
    season = None
    for el in list_soup.find_all(["h2", "h3", "tr"]):
        text = el.get_text(" ", strip=True)

        if el.name in ("h2", "h3"):
            m = re.match(r"Book\s+(One|Two|Three)\b", text, re.IGNORECASE)
            if m:
                season = BOOK_NUMBERS[m.group(1).lower()]
            continue

        cells = [c.get_text(" ", strip=True) for c in el.find_all(["th", "td"], recursive=False)]
        if not cells or season is None:
            continue
        # Title cell is first; the row must also contain numeric Chapter/Episode cells
        if norm(cells[0]) != norm(title):
            continue
        numbers = [int(c) for c in cells[1:] if c.isdigit()]
        if len(numbers) >= 2:
            return season, numbers[-2], numbers[-1]
    return None


# --- Fetch rendered article HTML via the API ---
parsed = fetch_page(PAGE)
soup = BeautifulSoup(parsed["text"], "html.parser")
content = soup.select_one("div.mw-parser-output") or soup

list_soup = BeautifulSoup(fetch_page(LIST_PAGE)["text"], "html.parser")
season_episode = lookup_in_episode_list(list_soup, EPISODE_TITLE)
if season_episode:
    SEASON, EPISODE_NUM, OVERALL_NUM = season_episode
else:
    SEASON = EPISODE_NUM = OVERALL_NUM = None
    print("WARNING: could not find this episode in the wiki's episode list.")
print(f"Episode: {EPISODE_TITLE} | season={SEASON} | episode={EPISODE_NUM} | overall={OVERALL_NUM}")


def clean(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)   # [stage directions]
    text = re.sub(r"\([^)]*\)", "", text)    # (Angrily)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text


# Matches a row that consists solely of "Fade to credits."
FADE_RE = re.compile(r"^\s*fade to credits\.?\s*$", re.IGNORECASE)
# Matches a heading that starts with the word "Cast"
CAST_RE = re.compile(r"^cast\b", re.IGNORECASE)

# --- Parse: walk headings and rows in document order ---
# Stop when we hit EITHER the "Fade to credits" row OR the "Cast" header.
rows = []
for el in content.find_all(["h2", "h3", "tr"]):
    text = el.get_text(" ", strip=True)

    if (el.name in ("h2", "h3") and CAST_RE.match(text)) or (
        el.name == "tr" and FADE_RE.match(text)
    ):
        break

    if el.name != "tr":
        continue  # other headings are ignored

    cells = el.find_all(["th", "td"], recursive=False)
    if len(cells) != 2:
        continue  # scene descriptions usually span the whole row

    character = cells[0].get_text(" ", strip=True).rstrip(":").strip()
    dialogue = clean(cells[1].get_text(" ", strip=True))

    if character and dialogue:
        rows.append(
            {
                "season": SEASON,
                "episode_number": EPISODE_NUM,
                "overall_episode": OVERALL_NUM,
                "episode_title": EPISODE_TITLE,
                "character": character,
                "dialogue": dialogue,
            }
        )

df = pd.DataFrame(rows)

# --- Build filename: s01e01_the_boy_in_the_iceberg.csv ---
slug = re.sub(r"[^a-z0-9]+", "_", EPISODE_TITLE.lower()).strip("_")
prefix = f"s{SEASON:02d}e{EPISODE_NUM:02d}_" if season_episode else ""
out_path = f"data/raw/{prefix}{slug}.csv"

os.makedirs("data/raw", exist_ok=True)
df.to_csv(out_path, index=False)
print(f"Saved {len(df)} rows to {out_path}")
