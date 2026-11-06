from pathlib import Path

import pandas as pd
import plotly.express as px

IN_PATH = Path("data/processed/all_episodes_final.csv")
OUT_PATH = Path("outputs/team_avatar_cumulative_word_count.html")

team_avatar = [
    "Aang",
    "Sokka",
    "Katara",
    "Toph",
    "Zuko"]

CHARACTER_COLORS = {
    # 2 Water Tribe
    "Sokka": "#003399",
    "Katara": "#000066",

    "Zuko": "#a90200",
    "Toph": "#036634",
    "Aang": "#ff6600"
}

def main():
    df = pd.read_csv(IN_PATH)

    team_avatar_df = df.loc[df['character'].isin(team_avatar)]

    fig = px.line(
    team_avatar_df,
    x='overall_episode',
    y='running_word_count',
    color='character',
    title='Running Word Count across Team Avatar Members',
    labels={
        "running_word_count": "Cumulative Word Count",
        "character": "Character",
        "overall_episode": "Overall Episode",
    },
    color_discrete_map=CHARACTER_COLORS,
    template="simple_white",
    )

    # Season ticks and dividers
    ticks = (
        team_avatar_df[['overall_episode', 'season', 'episode_number']]
        .drop_duplicates()
        .sort_values('overall_episode')
    )
    season_starts = ticks.groupby('season').first().reset_index()

    for x in season_starts['overall_episode'][1:]:
        fig.add_vline(
            x=x,
            line_color="black",
            line_width=1,
            line_dash="dot",
            layer="above",
        )

    fig.update_xaxes(
        tickmode='array',
        tickvals=season_starts['overall_episode'],
        ticktext=[f"Book {s}" for s in season_starts['season']],
    )

    # Direct labels instead of a legend
    fig.update_layout(showlegend=False, margin=dict(r=100))

    # Use the colors Plotly actually drew
    line_colors = {trace.name: trace.line.color for trace in fig.data}

    # Last data point per character, sorted bottom to top
    last_points = (
        team_avatar_df.sort_values('overall_episode')
        .groupby('character')
        .tail(1)
        .sort_values('running_word_count')
        .reset_index(drop=True)
    )

    # Minimum vertical gap between labels
    min_gap = 0.05 * last_points['running_word_count'].max()

    # Push each label up if it's too close to the one below it
    label_y = []
    for y in last_points['running_word_count']:
        if label_y and y < label_y[-1] + min_gap:
            y = label_y[-1] + min_gap
        label_y.append(y)
    last_points['label_y'] = label_y

    for _, row in last_points.iterrows():
        fig.add_annotation(
            x=row['overall_episode'],
            y=row['label_y'],
            text=row['character'],
            showarrow=False,
            xanchor='left',
            xshift=8,
            font=dict(color=line_colors[row['character']], size=13),
        )

    fig.show()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUT_PATH)

if __name__ == "__main__":
    main()