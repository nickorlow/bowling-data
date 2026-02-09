from loader import DataLoader
from calcs import Calculations
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import polars as ps
import os

env = Environment(loader=FileSystemLoader("assets/templates"))

data_files = [
    ("Susquehanna Winter 2026", "./backing-data/csv/susquehanna-winter2026.csv"),
    ("University of Texas Spring 2024", "./backing-data/csv/utexas-spring2024.csv"),
    ("Miscellaneous", "./backing-data/csv/misc.csv"),
]

root_template = env.get_template("layout.html")
gen_time = str(datetime.now())

season_files = []

combined_df = None
combined_stats_df = None

seasons = []

for data_file in data_files:
    df, stats_df = DataLoader.load_bowling_csv(data_file[1])
    if type(combined_df) == ps.DataFrame:
        combined_df.extend(df)
    else:
        combined_df = df.clone()
    if type(combined_stats_df) == ps.DataFrame:
        combined_stats_df.extend(stats_df)
    else:
        combined_stats_df = stats_df.clone()

    if "team" in df.columns:
        for team in df["team"].unique():
            if team != None:
                seasons.append(
                    (
                        df.filter(ps.col("team") == team),
                        stats_df.filter(ps.col("team") == team),
                        f"{data_file[0]} Team {team}",
                    )
                )

    seasons.append((df, stats_df, data_file[0]))

seasons.append((combined_df, combined_stats_df, "Combined"))

for df, stats_df, season_name in seasons:
    dirname = f"{season_name.replace(' ','_')}"
    filename = f"{dirname}/game.html"
    path = [(season_name, f"/{filename}")]

    game_dates = []
    calcs = Calculations(stats_df, df)
    games = calcs.individual_games

    for date in games["date"].unique().sort():
        game_dates.append(
            {
                "date": date.strftime("%b %d %Y"),
                "games": games.filter(ps.col("date") == date).rows(named=True),
            }
        )

    for game in games.rows(named=True):
        template = env.get_template("game.html")
        game_records = stats_df.filter(
            (ps.col("game_num") == game["game_num"]) & (ps.col("date") == game["date"])
        )
        player_games = []

        for bowler in game_records["bowler"].unique().sort():
            frames = []
            for frame in range(1, 11):
                throws = []
                for throw in game_records.filter(
                    (ps.col("bowler") == bowler) & (ps.col("frame") == frame)
                ).rows(named=True):
                    throws.append(throw)
                frames.append(throws)
            player_games.append({"bowler": bowler, "frames": frames})

        inner_output = template.render(game=game, player_games=player_games)
        game_filename = f"{game['date']}__{game['game_num']}.html"
        path.append(
            (f"{game['date']} game {game['game_num']}", f"/{dirname}/{game_filename}")
        )
        output = root_template.render(
            content=inner_output, path=path, gen_time=gen_time
        )
        path.pop()
        if not os.path.exists(f"gen-html/{dirname}"):
            os.mkdir(f"gen-html/{dirname}")
        with open(f"./gen-html/{dirname}/{game_filename}", "w") as f:
            f.write(output)

    template = env.get_template("season.html")
    inner_output = template.render(
        personal_high_score_df=calcs.stats,
        high_score_df=calcs.highest_scores(),
        wins_df=calcs.wins_matrix,
        fills_df=calcs.fills_df,
        pf_df=calcs.pinfall_df,
        game_dates=game_dates,
    )
    output = root_template.render(content=inner_output, path=path, gen_time=gen_time)
    if not os.path.exists(f"gen-html"):
        os.mkdir(f"gen-html")
    if not os.path.exists(f"gen-html/{dirname}"):
        os.mkdir(f"gen-html/{dirname}")

    season_files.append(
        (
            season_name,
            filename,
            df["bowler"].unique().count(),
            len(df),
            df["date"].sort().first(),
            df["date"].sort().last(),
        )
    )
    with open(f"./gen-html/{filename}", "w") as f:
        f.write(output)

index_template = env.get_template("seasons.html")
inner_output = index_template.render(data_files=season_files)
output = root_template.render(content=inner_output, path=[], gen_time=gen_time)
with open(f"./gen-html/index.html", "w") as f:
    f.write(output)

print("Generation completed")
