"""
Scrape every Avatar: The Last Airbender transcript listed on the wiki's
episode list page. Each episode is saved as its own CSV (resumable), and an
optional combined all_episodes.csv is built from those files at the end.
"""
import glob
import os
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

API_URL = "https://avatar.fandom.com/api.php"
HEADERS = {"User-Agent": "Mozilla/5.0"}
LIST_PAGE = "List_of_Avatar:_The_Last_Airbender_episodes"
OUT_DIR = "data/raw"
DELAY_SECONDS = 2          # pause between requests to be polite to the wiki
COMBINE_AT_END = False      # also write all_episodes.csv from the per-episode files

BOOK_NUMBERS = {"one": 1, "two": 2, "three": 3}

# Matches a row that consists solely of "Fade to credits."
FADE_RE = re.compile(r"^\s*fade to credits\.?\s*$", re.IGNORECASE)
# Matches a heading that starts with the word "Cast"
CAST_RE = re.compile(r"^cast\b", re.IGNORECASE)


def fetch_page(page: str) -> dict:
    """Fetch rendered HTML for a wiki page via the API."""
    params = {
        "action": "parse",
        "page": page,
        "prop": "text",
        "redirects": 1,
        "format": "json",
        "formatversion": 2,
    }
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "parse" not in data:
        raise RuntimeError(f"API did not return the page '{page}': {data.get('error', data)}")
    return data["parse"]


def clean(text: str) -> str:
    text = re.sub(r"\[[^\]]*\]", "", text)   # [stage directions]
    text = re.sub(r"\([^)]*\)", "", text)    # (Angrily)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text


def get_episode_list() -> list[dict]:
    """
    Parse the wiki's episode list. Headings like 'Book One: Water' set the
    season; table rows have the columns Title | Original air date |
    Chapter # | Episode #.
    """
    soup = BeautifulSoup(fetch_page(LIST_PAGE)["text"], "html.parser")

    episodes, seen = [], set()
    season = None
    for el in soup.find_all(["h2", "h3", "tr"]):
        text = el.get_text(" ", strip=True)

        if el.name in ("h2", "h3"):
            m = re.match(r"Book\s+(One|Two|Three)\b", text, re.IGNORECASE)
            if m:
                season = BOOK_NUMBERS[m.group(1).lower()]
            continue

        cells = el.find_all(["th", "td"], recursive=False)
        if not cells or season is None:
            continue

        texts = [c.get_text(" ", strip=True) for c in cells]
        numbers = [int(t) for t in texts[1:] if t.isdigit()]
        if len(numbers) < 2:
            continue  # synopsis rows, header rows, etc.

        # Prefer the link's page title (exact wiki title); fall back to cell text
        link = cells[0].find("a")
        title = (link.get("title") if link and link.get("title") else texts[0]).strip(' "“”')
        if not title or title in seen:
            continue
        seen.add(title)

        episodes.append(
            {
                "title": title,
                "season": season,
                "episode_number": numbers[-2],   # chapter within the book
                "overall_episode": numbers[-1],  # running count across the series
            }
        )
    return episodes


def scrape_transcript(title: str, season: int, episode_number: int, overall_episode: int) -> pd.DataFrame:
    """Scrape one episode's transcript into a DataFrame."""
    page = "Transcript:" + title.replace(" ", "_")
    soup = BeautifulSoup(fetch_page(page)["text"], "html.parser")
    content = soup.select_one("div.mw-parser-output") or soup

    # Walk headings and rows in document order. Stop at EITHER the
    # "Fade to credits" row OR the "Cast" header.
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
                    "season": season,
                    "episode_number": episode_number,
                    "overall_episode": overall_episode,
                    "episode_title": title,
                    "character": character,
                    "dialogue": dialogue,
                }
            )
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    episodes = get_episode_list()
    print(f"Found {len(episodes)} episodes in the list page.")

    for ep in episodes:
        label = f"S{ep['season']:02d}E{ep['episode_number']:02d} {ep['title']}"
        slug = re.sub(r"[^a-z0-9]+", "_", ep["title"].lower()).strip("_")
        path = os.path.join(OUT_DIR, f"s{ep['season']:02d}e{ep['episode_number']:02d}_{slug}.csv")

        if os.path.exists(path):  # already scraped on a previous run
            print(f"Exists, skipping: {path}")
            continue

        try:
            df = scrape_transcript(**ep)
        except Exception as e:
            print(f"SKIPPED {label}: {e}")
            time.sleep(DELAY_SECONDS)
            continue

        if df.empty:
            print(f"SKIPPED {label}: no dialogue rows found")
        else:
            df.to_csv(path, index=False)
            print(f"Saved {len(df):>4} rows -> {path}")

        time.sleep(DELAY_SECONDS)

    if COMBINE_AT_END:
        files = sorted(glob.glob(os.path.join(OUT_DIR, "s[0-9][0-9]e[0-9][0-9]_*.csv")))
        if files:
            combined = pd.concat(map(pd.read_csv, files), ignore_index=True)
            out = os.path.join(OUT_DIR, "all_episodes.csv")
            combined.to_csv(out, index=False)
            print(f"Combined {len(combined)} rows from {len(files)} files -> {out}")


if __name__ == "__main__":
    main()