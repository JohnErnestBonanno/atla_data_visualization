import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

IN_PATH = Path("data/processed/all_episodes_final.csv")
OUTPUT_DIR = Path("outputs/line_segment")

ETHNICITY_COLORS = {
    "Water Tribe": "#003399",
    "Fire Nation": "#a90200",
    "Earth Kingdom": "#036634",
    "Air Nomad": "#ff6600",
    "Kyoshi Islander": "#036634",
}

MISSING_COLOR = "#8c8c8c"  # medium gray, visible on white
MISSING_LABEL = "Unknown"


def plot_episode(df, season, episode_number, ethnicity_colors=ETHNICITY_COLORS,
                 missing_color=MISSING_COLOR, bar_width=0.6, padding=0.1):
    """
    Plot one episode as evenly spaced vertical bars, one per line of dialogue.
    Bar length = word count, centered on a shared midline.
    Color = ethnicity (gray if missing). Hover = character.

    bar_width: fraction of each slot the bar fills (0-1). Lower = more space
               between bars. At 0.6, the gap is always 40% of the slot width.
    """
    ep = df[(df['season'] == season) & (df['episode_number'] == episode_number)].copy()
    ep = ep.reset_index(drop=True)

    if ep.empty:
        raise ValueError(f"No rows found for Season {season}, Episode {episode_number}")

    episode_title = ep['episode_title'].iloc[0]

    # Blank or missing ethnicities become "Unknown"
    ep['ethnicity'] = (
        ep['ethnicity']
        .fillna(MISSING_LABEL)
        .replace(r'^\s*$', MISSING_LABEL, regex=True)
    )

    # Evenly spaced slot for every line of dialogue, in script order
    positions = ep.index.to_list()
    colors = [ethnicity_colors.get(eth, missing_color) for eth in ep['ethnicity']]
    hover = [
        f"{row.character}<br>{row.word_count} words"
        for row in ep.itertuples()
    ]

    fig = go.Figure(
        go.Bar(
            x=positions,
            y=ep['word_count'],
            base=-ep['word_count'] / 2,   # start each bar below the midline
            width=bar_width,              # in x-axis units, so the gap is guaranteed
            marker=dict(color=colors, line=dict(width=0)),
            hovertext=hover,
            hoverinfo='text',
        )
    )

    # Symmetric y-range sized to the longest line, plus padding
    y_limit = (ep['word_count'].max() / 2) * (1 + padding)

    fig.update_layout(
        title=dict(
            text=f"{episode_title}: Season {season}, Episode {episode_number}",
            x=0.5,
            xanchor="center",
        ),
        template="simple_white",
        showlegend=False,
        hovermode='closest',
        xaxis=dict(visible=False, range=[-1, len(ep)]),
        yaxis=dict(visible=False, range=[-y_limit, y_limit]),
    )

    return fig


def slugify(text):
    """'The Boy in the Iceberg' -> 'the_boy_in_the_iceberg'"""
    text = re.sub(r"[^\w\s-]", "", str(text).lower())  # drop punctuation
    return re.sub(r"[\s-]+", "_", text).strip("_")


def save_all_episodes(df, output_dir=OUTPUT_DIR, fmt="html", width=1400, height=700, scale=2):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)  # creates folders if missing

    episodes = (
        df[['season', 'episode_number', 'episode_title']]
        .drop_duplicates()
        .sort_values(['season', 'episode_number'])
    )

    for row in episodes.itertuples(index=False):
        fig = plot_episode(df, season=row.season, episode_number=row.episode_number)

        filename = f"s{row.season}_ep{row.episode_number:02d}_{slugify(row.episode_title)}.{fmt}"
        path = output_dir / filename

        if fmt == "html":
            fig.write_html(path)
        else:
            fig.write_image(path, width=width, height=height, scale=scale)

        print(f"Saved {path}")


def main():
    df = pd.read_csv(IN_PATH)
    save_all_episodes(df, output_dir=OUTPUT_DIR, fmt="html")


if __name__ == "__main__":
    main()