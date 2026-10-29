"""
Build data/processed/ethnicity_mapping.csv.

1. Take every unique character from all_episodes_word_counts.csv
2. Sort them by total words of dialogue (most talkative first)
3. Look each one up on the Avatar wiki and read the "Ethnicity" field
   from the character infobox
"""
import os
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

API_URL = "https://avatar.fandom.com/api.php"
HEADERS = {"User-Agent": "Mozilla/5.0"}
INPUT_PATH = "data/processed/all_episodes_word_counts.csv"
OUTPUT_PATH = "data/interim/ethnicity_mapping.csv"
DELAY_SECONDS = 1  # pause between requests to be polite to the wiki
TOP_N = None       # e.g. 50 to only look up the 50 most talkative characters


def get_character_totals() -> pd.DataFrame:
    """Unique characters with total words spoken, sorted most to least."""
    df = pd.read_csv(INPUT_PATH, usecols=["character", "word_count"])
    df["character"] = df["character"].astype("string").str.strip()
    df = df[df["character"].notna() & (df["character"] != "")]

    totals = (
        df.groupby("character", as_index=False)["word_count"].sum()
        .rename(columns={"word_count": "total_words"})
        .sort_values(["total_words", "character"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return totals


def fetch_character_page(name: str, session: requests.Session):
    """Return the parsed wiki page for a character, or None if it doesn't exist."""
    params = {
        "action": "parse",
        "page": name.replace(" ", "_"),
        "prop": "text",
        "redirects": 1,
        "format": "json",
        "formatversion": 2,
    }
    resp = session.get(API_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "parse" not in data:  # e.g. {"error": {"code": "missingtitle"}}
        return None
    return BeautifulSoup(data["parse"]["text"], "html.parser")


def extract_ethnicity(soup: BeautifulSoup):
    """
    Read the Ethnicity row of the character infobox.
    Returns (ethnicity or None, list of all infobox labels seen).
    """
    infobox = soup.select_one("aside.portable-infobox")
    if infobox is None:
        return None, []

    labels = [el.get_text(" ", strip=True) for el in infobox.select(".pi-data-label")]

    item = infobox.select_one('[data-source="ethnicity"]')
    if item is None:  # fall back to matching the visible label text
        for cand in infobox.select(".pi-data"):
            label = cand.select_one(".pi-data-label")
            if label and "ethnic" in label.get_text().lower():
                item = cand
                break
    if item is None:
        return None, labels

    value = item.select_one(".pi-data-value") or item
    for sup in value.select("sup"):   # footnote markers like [1]
        sup.decompose()
    for br in value.find_all("br"):   # multiple values are separated by <br>
        br.replace_with("; ")

    text = value.get_text(" ", strip=True)
    text = re.sub(r"\s*;\s*", "; ", text).strip("; ").strip()
    return (text or None), labels


def main():
    totals = get_character_totals()
    if TOP_N:
        totals = totals.head(TOP_N)
    print(f"{len(totals)} unique characters to look up.")

    results = []
    printed_labels = False
    session = requests.Session()

    try:
        for i, row in enumerate(totals.itertuples(index=False), start=1):
            name = row.character
            ethnicity, status = None, "no_page"

            try:
                soup = fetch_character_page(name, session)
            except Exception as e:
                soup, status = None, f"error: {e}"

            if soup is not None:
                ethnicity, labels = extract_ethnicity(soup)
                if not labels:
                    status = "no_infobox"
                elif ethnicity is None:
                    status = "no_ethnicity_field"
                else:
                    status = "ok"

                if labels and not printed_labels:  # one-time check of the infobox layout
                    print(f"Infobox fields seen on '{name}': {labels}")
                    printed_labels = True

            results.append(
                {
                    "character": name,
                    "total_words": row.total_words,
                    "ethnicity": ethnicity,
                    "status": status,
                }
            )
            print(f"[{i}/{len(totals)}] {name}: {ethnicity or status}")
            time.sleep(DELAY_SECONDS)
    finally:
        # Runs even on Ctrl+C, so a partial run still gets saved
        if results:
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            out = pd.DataFrame(results)
            out.to_csv(OUTPUT_PATH, index=False)
            found = (out["status"] == "ok").sum()
            print(f"\nSaved {len(out)} rows -> {OUTPUT_PATH} ({found} with an ethnicity)")


if __name__ == "__main__":
    main()
