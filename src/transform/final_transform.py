"""
Final transform:
1. Map ethnicity (data/interim/map_ethnicity.csv) onto all_episodes_word_counts.csv
2. Add a running total of words spoken, per character, across all rows
"""
import os

import pandas as pd

WORD_COUNTS_PATH = "data/interim/all_episodes_word_counts.csv"
MAPPING_PATH = "data/interim/ethnicity_mapping.csv"
OUTPUT_PATH = "data/processed/all_episodes_final.csv"


def main():
    df = pd.read_csv(WORD_COUNTS_PATH)
    mapping = pd.read_csv(MAPPING_PATH)

    # --- Prepare the mapping: one ethnicity per character ---
    missing_cols = {"character", "ethnicity"} - set(mapping.columns)
    if missing_cols:
        raise KeyError(f"{MAPPING_PATH} is missing column(s): {sorted(missing_cols)}")

    mapping = mapping[["character", "ethnicity"]].copy()
    mapping["character"] = mapping["character"].astype("string").str.strip()
    df["character"] = df["character"].astype("string").str.strip()

    # --- Map ethnicity onto every row (left join keeps all dialogue rows) ---
    # validate="m:1" raises an error if the mapping lists a character twice,
    # instead of silently duplicating dialogue rows.
    df = df.merge(mapping, on="character", how="left", validate="m:1")

    unmapped = df.loc[df["ethnicity"].isna(), "character"]
    if len(unmapped):
        print(f"{unmapped.nunique()} characters have no ethnicity ({len(unmapped):,} rows). Top unmapped by words:")
        top = (
            df[df["ethnicity"].isna()]
            .groupby("character")["word_count"].sum()
            .nlargest(10)
        )
        print(top.to_string())

    # --- Running total of words per character, in story order ---
    # Stable sort keeps the original line order inside each episode.
    df = df.sort_values("overall_episode", kind="stable").reset_index(drop=True)
    df["running_word_count"] = df.groupby("character")["word_count"].cumsum()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved {len(df):,} rows -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
