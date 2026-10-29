from pathlib import Path
import pandas as pd
import plotly.express as px

IN_PATH = Path('data/processed/all_episodes_final.csv')
OUT_PATH = Path('outputs/top_10_characters_by_lines.html')


def main():
    df = pd.read_csv(IN_PATH)

    top_characters = (
        df
        .groupby("character", as_index=False)
        .agg(
            line_count=("character", "size"),
            word_count=("word_count", "sum"),
        )
        .nlargest(10, "word_count")
        .sort_values("word_count")   # ascending: Plotly draws the first row at the bottom
    )

    fig = px.bar(
        top_characters,
        x="word_count",
        y="character",
        orientation="h",
        text="word_count",
        title="Top 10 Characters by Number of Words",
        labels={"word_count": "Words", "character": "Character"},
    )
    fig.show()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_PATH)
    # fig.write_image(OUT_PATH.with_suffix('.png'))  # static version, needs kaleido


if __name__ == '__main__':
    main()