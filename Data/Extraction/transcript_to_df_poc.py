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


# --- Parse: table rows with a speaker cell and a dialogue cell ---
rows = []
for tr in content.find_all("tr"):
    cells = tr.find_all(["th", "td"], recursive=False)
    if len(cells) != 2:
        continue  # scene descriptions usually span the whole row

    character = cells[0].get_text(" ", strip=True).rstrip(":").strip()
    dialogue = clean(cells[1].get_text(" ", strip=True))

    if character and dialogue:
        rows.append({"character": character, "dialogue": dialogue})

df = pd.DataFrame(rows)

if df.empty:
    # Diagnostic: show the HTML around the first line of dialogue
    hit = content.find(string=re.compile(r"It's not getting away from me"))
    print("No dialogue rows found. Markup around a known line:")
    if hit:
        print(hit.parent.parent.parent.prettify()[:1500])
    else:
        print("Couldn't locate the line either; check the page title:", PAGE)
else:
    print(df.head(10))
    print(df["character"].value_counts())