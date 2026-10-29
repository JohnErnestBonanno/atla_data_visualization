"""
Combine the per-episode CSVs in data/raw into one DataFrame, drop the
unaired pilot (episode 00), and add a word count for each dialogue row.
"""
import glob
import os

import pandas as pd

RAW_DIR = "data/raw"
OUT_DIR = "data/interim"
OUT_FILE = "all_episodes_word_counts.csv"

# Matches s01e02_the_avatar_returns.csv but NOT all_episodes.csv
PATTERN = os.path.join(RAW_DIR, "s[0-9][0-9]e[0-9][0-9]_*.csv")


def main():
    files = sorted(glob.glob(PATTERN))
    if not files:
        raise FileNotFoundError(f"No episode CSVs found matching {PATTERN}")

    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    print(f"Loaded {len(df):,} rows from {len(files)} files.")

    # Drop the unaired pilot (episode 00)
    before = len(df)
    df = df[df["episode_number"] != 0].reset_index(drop=True)
    print(f"Dropped {before - len(df):,} rows from episode 00.")

    # Words per row: split on whitespace and count the pieces
    df["word_count"] = df["dialogue"].fillna("").str.split().str.len()

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, OUT_FILE)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df):,} rows -> {out_path}")

    # Quick sanity check
    print("\nTop 10 characters by total words:")
    print(df.groupby("character")["word_count"].sum().nlargest(10))


if __name__ == "__main__":
    main()
