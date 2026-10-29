from pathlib import Path

import pandas as pd
import plotly.express as px

IN_PATH = Path("data/processed/all_episodes_final.csv")
OUT_PATH = Path("outputs/top_10_characters_by_words.html")

ETHNICITY_COLORS = {
    "Water Tribe": "#003399",
    "Fire Nation": "#a90200",
    "Earth Kingdom": "#036634",
    "Air Nomad": "#ff9900",
    "Kyoshi Islander": "#036634"
}


def main():
    df = pd.read_csv(IN_PATH)

    top_characters = (
        df
        .groupby(["character", "ethnicity"], as_index=False)
        .agg(
            line_count=("character", "size"),
            word_count=("word_count", "sum"),
        )
        .nlargest(10, "word_count")
        .sort_values("word_count", ascending=False)  # ascending: Plotly draws the first category at the bottom
    )

    fig = px.bar(
    top_characters,
    x="word_count",
    y="character",
    orientation="h",
    color="ethnicity",
    color_discrete_map=ETHNICITY_COLORS,
    text="word_count",
    title="Top 10 Characters in Avatar the Last Airbender by Word Count",
    labels={"word_count": "Words", "character": "Character", "ethnicity": "Ethnicity"},
    template="simple_white",                 # white background, no gridlines
    )
    
    fig.update_traces(texttemplate="%{x:,}", textposition="outside", cliponaxis=False)

    # Remove ink that repeats what the labels already say
    fig.update_xaxes(visible=False)              # the bars are labelled, so the axis is redundant
    fig.update_yaxes(title=None, showline=False, ticks="", categoryorder="total ascending")

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text=None,
        legend=dict(orientation="h", y=1.02, x=0),   # small legend above the bars
        bargap=0.35,
    )
    
    fig.show()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_PATH)
    # fig.write_image(OUT_PATH.with_suffix(".png"))  # static version, needs kaleido


if __name__ == "__main__":
    main()