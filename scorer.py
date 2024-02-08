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


data = pd.read_csv("data.csv")

for i, row in data.iterrows():
    score = 0
    strike_cnt = 0
    spare_cnt = 0
    foul_cnt = 0
    frame_scores = []

    bowler_name = row["bowler"]
    if (not row["throwdata_avail"]):
        continue

    for i in range(0, 84):
        if ((i % 8 == 0 and i != 80) or i == 83):
            print("+", end="")
        else:
            print("-", end="")
    print()
    print("| ", end="")
    for frame_idx in range(9, 28, 2):
        first_throw = False
        frame_number = int(((frame_idx - 9) / 2) + 1);

        first_throw = row[frame_idx]
        second_throw = row[frame_idx + 1]

        first_throw = score_of(first_throw)

        if (first_throw == 10):
            # Strike
            print("    X", end="")
            score += 10
            strike_cnt += 1
            next_throw_idx = next_throw(row, frame_idx)
            sb = score;
            score += score_of(row[next_throw_idx])
            if (frame_number == 10):
                if (score_of(row[next_throw_idx]) == 10):
                    strike_cnt += 1
            next_throw_idx = next_throw(row, next_throw_idx)
            score += score_of(row[next_throw_idx])
            if (frame_number == 10):
                if (score_of(row[next_throw_idx]) == 10):
                    strike_cnt += 1
                elif (sb == score - 10):
                    spare_cnt += 1
        else:
            second_throw = score_of(second_throw)
            if ((first_throw + second_throw) == 10):
                # Spare
                print(f"{first_throw:>2}  /", end="")
                spare_cnt += 1
                score += 10
                next_throw_idx = next_throw(row, frame_idx + 1)
                score += score_of(row[next_throw_idx])
                if (frame_number == 10):
                    if (score_of(row[next_throw_idx]) == 10):
                        strike_cnt += 1
            else:
                print(f"{first_throw:>2} {second_throw:>2}", end="")
                score += first_throw + second_throw
        frame_scores.append(score)
        print(" | ", end="")



    print()
    for i in range(0, 84):
        if ((i % 8 == 0 and i != 80) or i == 83):
            print("|", end="")
        else:
            print(" ", end="")
    print()
    print("| ", end="")
    for i in range(0, 10):
        print(str(frame_scores[i]).rjust(5 if i != 9 else 8, " "), end="")
        print(" | ", end="")
    print()
    for i in range(0, 84):
        if ((i % 8 == 0 and i != 80) or i == 83):
            print("+", end="")
        else:
            print("-", end="")
    print()
    print("{}  /// Score  : {} /  Strikes: {} / Spares : {}\n".format(bowler_name, score, strike_cnt, spare_cnt))
