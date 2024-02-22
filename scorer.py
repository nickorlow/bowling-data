import pandas as pd


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


def print_game(date, game_num, full_data):
    file = open(f"{date}_{game_num}.html", "w")
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

        if (not row["throwdata_avail"]):
            continue
        file.write(f"<td>{bowler_name}</td>")
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
    file.write("<h1>All Games</h1>")
    unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)
    for item in unique_combinations.iterrows():
        date = item[1].date
        game_num = item[1].game_num
        file.write(f"<a href=\"./{date}_{game_num}.html\">Game #{game_num} on {date}</a><br/>")
    file.close()

data = pd.read_csv("data.csv")
unique_combinations = data.groupby(['date', 'game_num']).size().reset_index().drop(0, axis=1)

for item in unique_combinations.iterrows():
    print_game(item[1].date, item[1].game_num, data)

print_games_index(data)
