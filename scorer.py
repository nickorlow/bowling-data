import pandas as pd
from scipy import stats
from datetime import datetime
import os


def next_throw(row, i):
    i += 1
    while (str(row[i]) == "nan"):
        i += 1
    return i

def score_of(x):
    if (x == "F"):
        return 0
    if (str(x) == "nan"):
        print("NaN unexpected")
        exit(1)
    return int(x)

def make_table(name, df, modifier):
    df = modifier(df)
    tablestr = "<table style=\"margin:5px;\">"
    tablestr += f"<tr><th colspan=\"{len(df.iloc[0])}\">{name}</th></tr>"
    
    if 'rank' in df.columns:
        tablestr += "<tr><th>Rank</th><th>Bowler</th><th>Average</th><th>Confidence Interval</th><th>Lower Bound</th><th>Upper Bound</th></tr>"
    else:
        tablestr += "<tr>"
        for col in df.columns:
            tablestr += f"<th>{col}</th>"
        tablestr += "</tr>"

    for i, row in df.iterrows():
        tablestr += f"<tr>"
        rowlist = list(row)
        for col in rowlist:
            tablestr += f"<td>{col}</td>"
        tablestr += f"</tr>"
    tablestr += """
    </table>
    <style>
    table, th, td {
        border: 1px solid;
    }
    td {
        padding: 4px;
    }
    </style>"""
    return tablestr


wins_count = {}
def count_wins(dataframe):
    
    for index, row in dataframe.iterrows():
        bowler = row['bowler']
        score = row['score']
        date = row['date'].strftime('%m-%d-%Y')
        game_num = row['game_num']
        
        game_id = f"{date}-{game_num}"
        
        if game_id not in wins_count:
            wins_count[game_id] = {'bowler': None, 'score': 0}
        
        if game_id not in wins_count or score >= wins_count[game_id]['score']:
            if (score == wins_count[game_id]['score']):
                wins_count[game_id] = {'bowler': None, 'score': score}
            else:
                wins_count[game_id] = {'bowler': bowler, 'score': score}

    
    bowlers_wins = {}

    for bowler in dataframe['bowler'].unique():
        bowlers_wins[bowler] = 0

    for game_id in wins_count:
        info = wins_count[game_id]
        winning_bowler = info['bowler']
        if winning_bowler != None:
            bowlers_wins[winning_bowler] += 1

    bw_df = pd.DataFrame(list(bowlers_wins.items()), columns=['bowler', 'wins']).sort_values(by=['wins'], ascending=0)

    return bw_df

def print_game(date, game_num, full_data, file):
    file = open(f"gen-html/{file}/{date.strftime('%m-%d-%Y')}_{game_num}.html", "w")
    data = full_data[full_data['date'] == date]
    data = data[data['game_num'] == game_num]
    data = data.sort_values(by=['bowler'])
    file.write(f"<h1>Game #{game_num} on {date.strftime('%m-%d-%Y')} at {data.iloc[0]['location']}</h1>")
    file.write("<table>")
    for i, row in data.iterrows():
        file.write("<tr>")
        score = 0
        strike_cnt = 0
        spare_cnt = 0
        frame_scores = []
        bowler_name = row["bowler"]

        game_num = row["game_num"]
        date = row["date"]

        file.write(f"<td>{bowler_name}</td>")
        if (row["throwdata_avail"]):
            for frame_idx in range(9, 28, 2):
                file.write("<td>")
                first_throw = False
                frame_number = int(((frame_idx - 9) / 2) + 1)

                first_throw = row[frame_idx]
                second_throw = row[frame_idx + 1]
                first_throw = score_of(first_throw)
                if (first_throw == 10):
                    # Strike
                    file.write(" X ")
                    score += 10
                    strike_cnt += 1
                    next_throw_idx = next_throw(row, frame_idx)
                    sb = score;
                    score += score_of(row[next_throw_idx])
                    if (frame_number == 10):
                        if (score_of(row[next_throw_idx]) == 10):
                            file.write(" X ")
                            strike_cnt += 1
                        else:
                            file.write(f" {score_of(row[next_throw_idx])} ")
                    next_throw_idx = next_throw(row, next_throw_idx)
                    score += score_of(row[next_throw_idx])
                    if (frame_number == 10):
                        if (score_of(row[next_throw_idx]) == 10):
                            file.write(" X ", end="")
                            strike_cnt += 1
                        elif (sb == score - 10 and score_of(row[next_throw_idx]) != 0):
                            file.write(" /")
                            spare_cnt += 1
                        else:
                            file.write(f" {score_of(row[next_throw_idx])} ")
                else:
                    second_throw = score_of(second_throw)
                    if ((first_throw + second_throw) == 10):
                        # Spare
                        file.write(f"{first_throw:>2}  /")
                        spare_cnt += 1
                        score += 10
                        next_throw_idx = next_throw(row, frame_idx + 1)
                        score += score_of(row[next_throw_idx])
                        if (frame_number == 10):
                            if (score_of(row[next_throw_idx]) == 10):
                                strike_cnt += 1
                    else:
                        file.write(f"{first_throw:>2} {second_throw:>2}")
                        score += first_throw + second_throw
                file.write(f"<br/>{score}")
                frame_scores.append(score)
                file.write("</td>")
        else:
            file.write("<td colspan=\"10\">No throw data availiable</td>")
        file.write(f"<td><b>{row['score']}</b></td>")
        file.write("</tr>")
    file.write("</table>")
    file.write("""
    <style>
    table, th, td {
        border: 1px solid;
    }
    td {
        padding: 4px;
    }
    </style>""")
    file.close()

def print_games_index(data, file):
    file = open(f"gen-html/{file}/index.html", "w")

    file.write("<body>")
    file.write("<h1 style=\"margin-bottom: 0px;\">BART - Bowling Analysis and Research Tool</h1>")
    file.write("<p style=\"margin-top: 0px;\"><i>Not the Bay Area Rapid Transit Authority</i></p>")

    file.write("<div style=\"display: flex\">")

    def get_rankings(df):
        df_sorted = df.sort_values(by=['date', 'game_num'])
        dfg = df_sorted.groupby('bowler').tail(8)
        res = dfg.groupby("bowler")["score"].agg(['mean', 'sem']).reset_index()
        res['ci'] = res['sem'].apply(lambda x: f"&plusmn; {stats.norm.ppf(0.975) * x:.2f}")
        res['lower_bound'] = res.apply(lambda x: x['mean'] - float(x['ci'].split(" ")[1]), axis=1)
        res['upper_bound'] = res.apply(lambda x: x['mean'] + float(x['ci'].split(" ")[1]), axis=1)
        res['mean'] = res['mean'].round(3)
        res['lower_bound'] = res['lower_bound'].round(3)
        res['upper_bound'] = res['upper_bound'].round(3)
        res = res.sort_values(by='mean', ascending=False)
        
        res['rank'] = range(1, len(res) + 1)
        
        res['rank'] = res['rank'].astype(int)
        return res[['rank', 'bowler', 'mean', 'ci', 'lower_bound', 'upper_bound']]
    
    file.write(make_table("Ranking (Avg score of last 8 games)", data, get_rankings))

    def get_head_to_head_wins(df):
        # Get unique bowlers
        bowlers = df['bowler'].unique()
        
        # Create an empty dataframe for results
        result_df = pd.DataFrame(0, index=bowlers, columns=['Bowler'] + list(bowlers))
        
        # Fill the 'Bowler' column with the index (bowler names)
        result_df['Bowler'] = result_df.index
        
        # Group the dataframe by date and game_num
        grouped = df.groupby(['date', 'game_num'])
        
        # Iterate through each game
        for _, game_df in grouped:
            # Get bowlers and scores for this game
            game_results = game_df.set_index('bowler')['score']
            
            # Compare each pair of bowlers
            for bowler1 in game_results.index:
                for bowler2 in game_results.index:
                    if bowler1 != bowler2:
                        if game_results[bowler1] > game_results[bowler2]:
                            result_df.loc[bowler1, bowler2] += 1
                        elif game_results[bowler1] < game_results[bowler2]:
                            result_df.loc[bowler1, bowler2] -= 1
        
        return result_df


    def get_average_scores(df):
        highest_scores = df.groupby('bowler')['score'].mean().reset_index()
        return highest_scores.sort_values(by='score', ascending=False)
    def get_highest_scores(df):
        highest_scores = df.groupby('bowler')['score'].max().reset_index()
        return highest_scores.sort_values(by='score', ascending=False)
    file.write(make_table("Highest Scores", data, get_highest_scores))
    
    def get_strikes(df):
        lowest_scores = df.groupby('bowler')['strike_cnt'].sum().astype(int).reset_index()
        return lowest_scores.sort_values(by='strike_cnt', ascending=False)
    file.write(make_table("Most Strikes", data, get_strikes))

    def get_spares(df):
        lowest_scores = df.groupby('bowler')['spare_cnt'].sum().astype(int).reset_index()
        return lowest_scores.sort_values(by='spare_cnt', ascending=False)
    file.write(make_table("Most Spares", data, get_spares))
    
    file.write(make_table("Most Wins", data, count_wins))
    file.write(make_table("Average Score", data, get_average_scores))

    file.write("</div>")
    file.write("<div>")
    file.write(make_table("Head to Head (bowlers on left have net wins over bowlers on top)", data, get_head_to_head_wins))

    file.write("</div>")

    unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1).sort_values(by=['date', 'game_num'])
    file.write("<p><i>Confidence intervals calculated using the standard error of the mean and a 95% confidence level (z-score of 1.96).</i></p>")
    file.write("<h2>Game History</h2>")
    file.write("<div style=\"display: flex; flex-wrap: wrap;\">")
    ld = ""
    for item in unique_combinations.iterrows():
        date = item[1].date.strftime('%m-%d-%Y')
        if (ld != date):
            if (ld != ""):
                file.write("</div>")
            file.write(f"<div style=\"margin: 5px; min-width: max-content; padding: 5px;\"><h4>{date}</h4>")
        ld = date
        game_num = item[1].game_num
        game_id = f"{date}-{game_num}"
        winner = wins_count[game_id]['bowler']
        if (winner == None):
            winner = "tie"
        file.write(f"<a href=\"./{date}_{game_num}.html\">Game #{game_num} ({winner})</a><br/>")
    file.write("</div></div>")
    file.write("<hr/>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Data current as of {datetime.now().strftime('%m-%d-%Y at %H:%M:%S')}</p>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Hosted on <a href=\"https://nws.nickorlow.com\">NWS</a></p>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Powered by <a href=\"https://github.com/nickorlow/anthracite\">Anthracite Web Server</a></p>")
    file.write("</body>")
    file.close()

if not os.path.exists("gen-html"):
    os.mkdir("gen-html")
index_file = open(f"./gen-html/index.html", "w")
index_file.write("<body>")
index_file.write("<h1 style=\"margin-bottom: 0px;\">BART - Bowling Analysis and Research Tool</h1>")
index_file.write("<p style=\"margin-top: 0px;\"><i>Not the Bay Area Rapid Transit Authority</i></p>")
all_dfs = []

files = {
        "UT Austin - Spring 2024 (Austin, TX)": "utexas-spring2024.csv",
        "Susquehanna - Summer 2024 (Philadelphia, PA)": "susquehanna-summer2024.csv",
        "Unattached Bowling Records": "misc.csv"
        }

for (name, file) in files.items():
    if file.endswith(".csv"):
        wins_count = {}
        dirname = file.replace(".csv", "")
        index_file.write(f"<p><a href=\"{dirname}/index.html\">{name}</a></p>")
        print(dirname)
        if not os.path.exists("gen-html/"+dirname):
            os.mkdir("gen-html/"+dirname)
        data = pd.read_csv(file)
        data['date'] = pd.to_datetime(data['date'], format='%m-%d-%Y')
        unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)
        
        for item in unique_combinations.iterrows():
            print_game(item[1].date, item[1].game_num, data, dirname)
        
        print_games_index(data, dirname)
        all_dfs.append(data)

if not os.path.exists("gen-html/combined"):
    os.mkdir("gen-html/combined")
data = pd.concat(all_dfs, axis=0, ignore_index = True)
data['date'] = pd.to_datetime(data['date'], format='%m-%d-%Y')

unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)

for item in unique_combinations.iterrows():
    print_game(item[1].date, item[1].game_num, data, "combined")

print_games_index(data, "combined")

index_file.write(f"<p><a href=\"combined/index.html\">Combined Results from All Seasons</a></p>")
index_file.write("<hr/>")
index_file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Data current as of {datetime.now().strftime('%m-%d-%Y at %H:%M:%S')}</p>")
index_file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Hosted on <a href=\"https://nws.nickorlow.com\">NWS</a></p>")
index_file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Powered by <a href=\"https://github.com/nickorlow/anthracite\">Anthracite Web Server</a></p>")
index_file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Read the BART rules <a href=\"rules.html\">here</a></p>")
index_file.write(f"<script>if(!new URL(window.location.href).searchParams.get(\"af\")||new URL(window.location.href).searchParams.get(\"af\")===\"true\")window.location.href=\"./assets/april_fools.html\";</script>")
index_file.write("</body>")
index_file.close()


