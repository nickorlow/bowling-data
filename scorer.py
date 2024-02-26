import pandas as pd
from datetime import datetime


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

def print_game(date, game_num, full_data):
    file = open(f"{date.strftime('%m-%d-%Y')}_{game_num}.html", "w")
    data = full_data[full_data['date'] == date]
    data = data[data['game_num'] == game_num]
    data = data.sort_values(by=['bowler'])
    file.write(f"<h1>Game #{game_num} on {date}</h1>")
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

def print_games_index(data):
    file = open(f"index.html", "w")

    file.write("<body>")
    file.write("<h1 style=\"margin-bottom: 0px;\">BART - Bowling Analysis and Research Tool</h1>")
    file.write("<p style=\"margin-top: 0px;\"><i>Not the Bay Area Rapid Transit Authority</i></p>")

    file.write("<div style=\"display: flex\">")

    def get_rankings(df):
        df_sorted = df.sort_values(by=['date', 'game_num'])
        dfg = df_sorted.groupby('bowler').tail(8)
        res = dfg.groupby("bowler")["score"].mean().reset_index().sort_values(by='score', ascending=False).round(3)
        return res

    file.write(make_table("Ranking (Avg score of last 8 games)", data, get_rankings))

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

    file.write("</div>")

    unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)
    file.write("<h2>Game History</h2>")
    file.write("<div style=\"display: flex;\">")
    ld = ""
    for item in unique_combinations.iterrows():
        date = item[1].date.strftime('%m-%d-%Y')
        if (ld != date):
            if (ld != ""):
                file.write("</div>")
            file.write(f"<div style=\"margin: 5px;\"><h4>{date}</h4>")
        ld = date
        game_num = item[1].game_num
        file.write(f"<a href=\"./{date}_{game_num}.html\">Game #{game_num}</a><br/>")
    file.write("</div></div>")
    file.write("<hr/>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Data current as of {datetime.now().strftime('%m-%d-%Y at %H:%M:%S')}</p>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Hosted on <a href=\"https://nws.nickorlow.com\">NWS</a></p>")
    file.write(f"<p style=\"margin-bottom: 0px; margin-top: 0px;\">Powered by <a href=\"https://github.com/nickorlow/anthracite\">Anthracite Web Server</a></p>")
    file.write("</body>")
    file.close()

data = pd.read_csv("data.csv")
data['date'] = pd.to_datetime(data['date'], format='%m-%d-%Y')
unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)

for item in unique_combinations.iterrows():
    print_game(item[1].date, item[1].game_num, data)

print_games_index(data)


