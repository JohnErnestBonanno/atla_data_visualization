import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

API_URL = "https://avatar.fandom.com/api.php"
PAGE = "Transcript:The_Boy_in_the_Iceberg"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --- Fetch rendered article HTML via the API ---
params = {
    "action": "parse",
    "page": PAGE,
    "prop": "text",
    "format": "json",
    "formatversion": 2,
}
resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
resp.raise_for_status()
data = resp.json()
if "parse" not in data:
    raise RuntimeError(f"API did not return the page: {data}")

soup = BeautifulSoup(data["parse"]["text"], "html.parser")
content = soup.select_one("div.mw-parser-output") or soup


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
        rows.append({"character": character, "dialogue": dialogue})

df = pd.DataFrame(rows)

os.makedirs("data/raw", exist_ok=True)
df.to_csv("data/raw/poc.csv", index=False)