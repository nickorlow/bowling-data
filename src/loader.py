import polars as ps
from datetime import datetime


class DataLoader:
    ingest_schema = {
        "bowler": ps.String,
        "date": ps.String,
        "location": ps.String,
        "game_num": ps.Int32,
        "throwdata_avail": ps.Boolean,
        "score": ps.Int16,
        "strike_cnt": ps.Int16,
        "spare_cnt": ps.Int16,
        "foul_cnt": ps.Int16,
        "f1_t1": ps.String,
        "f1_t2": ps.String,
        "f2_t1": ps.String,
        "f2_t2": ps.String,
        "f3_t1": ps.String,
        "f3_t2": ps.String,
        "f4_t1": ps.String,
        "f4_t2": ps.String,
        "f5_t1": ps.String,
        "f5_t2": ps.String,
        "f6_t1": ps.String,
        "f6_t2": ps.String,
        "f7_t1": ps.String,
        "f7_t2": ps.String,
        "f8_t1": ps.String,
        "f8_t2": ps.String,
        "f9_t1": ps.String,
        "f9_t2": ps.String,
        "f10_t1": ps.String,
        "f10_t2": ps.String,
        "f10_t3": ps.String,
        "team": ps.String,
    }

    throw_dtype = ps.Struct({"foul": ps.Boolean, "pins_hit": ps.Int64})

    def parse_throw(x: str) -> throw_dtype:
        if x == "F":
            return {"foul": True, "pins_hit": 0}
        else:
            return {"foul": False, "pins_hit": int(x)}

    def get_flat_throws(df: ps.DataFrame) -> ps.Series:
        throw_exprs = []
        for frame_idx in range(1, 11):
            for throw_idx in range(1, 3 if frame_idx != 10 else 4):
                col_name = f"f{frame_idx}_t{throw_idx}"
                throw_exprs.append(ps.col(col_name).struct.field("pins_hit"))
        return df.select(
            ps.concat_list(throw_exprs).list.drop_nulls().alias("flat_throws")
        )["flat_throws"]

    def handle_frame_ten_strike(
        score, nt, nnt, frames, throws, scores, spares, strikes, pins_hit
    ):
        if nt + nnt == 10 and nt != 10 and nnt != 10:
            for i in range(1, 3):
                frames.append(10)
                throws.append(i)
                scores.append(score)
                spares.append(i == 2)
                strikes.append(False)
                pins_hit.append(nt if i == 1 else nnt)
        else:
            frames.append(10)
            throws.append(1)
            scores.append(score)
            spares.append(False)
            strikes.append(nt == 10)
            pins_hit.append(nt)

            frames.append(10)
            throws.append(2)
            scores.append(score)
            spares.append(False)
            strikes.append(nnt == 10)
            pins_hit.append(nnt)

    def calculate_stats_game(df) -> ps.DataFrame:
        score = 0
        throw_global_idx = 0
        frames, throws, scores, strikes, spares, pins_hit = [], [], [], [], [], []
        for frame_idx in range(1, 11):
            for throw_idx in range(1, 3):
                frame_col_name = f"f{frame_idx}_t{throw_idx}"
                if df[frame_col_name] == None:
                    continue
                ph = df[frame_col_name]["pins_hit"]
                pins_hit.append(ph)
                score += ph
                frames.append(frame_idx)
                throws.append(throw_idx)
                if throw_idx == 1 and ph == 10:
                    strikes.append(True)
                    next_throw = df["flat_throws"][throw_global_idx + 1]
                    nnext_throw = df["flat_throws"][throw_global_idx + 2]
                    score += next_throw + nnext_throw
                    if frame_idx == 10:
                        DataLoader.handle_frame_ten_strike(
                            score,
                            next_throw,
                            nnext_throw,
                            frames,
                            throws,
                            scores,
                            spares,
                            strikes,
                            pins_hit,
                        )
                        scores.append(score)
                        spares.append(False)
                        break
                else:
                    strikes.append(False)
                if (
                    throw_idx == 2
                    and (ph + df["flat_throws"][throw_global_idx - 1]) == 10
                ):
                    next_throw = df["flat_throws"][throw_global_idx + 1]
                    score += next_throw
                    spares.append(True)
                    if frame_idx == 10 and next_throw == 10:
                        frames.append(frame_idx)
                        throws.append(throw_idx + 1)
                        scores.append(score)
                        spares.append(False)
                        strikes.append(True)
                        pins_hit.append(next_throw)
                else:
                    spares.append(False)
                scores.append(score)
                throw_global_idx += 1
        odf = ps.DataFrame(
            {
                "bowler": df["bowler"],
                "game_num": df["game_num"],
                "date": df["date"],
                "frame": frames,
                "throw": throws,
                "score": scores,
                "strike": strikes,
                "spare": spares,
                "pins_hit": pins_hit,
                "team": df["team"],
            }
        )

        if df["score"] != score:
            print(
                f"score mismatch for {df['bowler']} {df['date']} {df['game_num']} c/g {score}/{df['score']}"
            )
            with ps.Config(tbl_cols=-1, tbl_rows=-1):
                print(odf)
            raise
        if df["strike_cnt"] != odf["strike"].sum():
            print(
                f"strike mismatch for {df['bowler']} {df['date']} {df['game_num']} c/g {odf['strike'].sum()}/{df['strike_cnt']}"
            )
            with ps.Config(tbl_cols=-1, tbl_rows=-1):
                print(odf)
            raise
        if df["spare_cnt"] != odf["spare"].sum():
            print(
                f"spare mismatch for {df['bowler']} {df['date']} {df['game_num']} c/g {odf['spare'].sum()}/{df['spare_cnt']}"
            )
            with ps.Config(tbl_cols=-1, tbl_rows=-1):
                print(odf)
            raise
        return odf

    def calculate_stats(df) -> ps.DataFrame:
        flat_throws = DataLoader.get_flat_throws(df)
        df = df.with_columns(flat_throws.alias("flat_throws"))
        rdf = None  # ps.DataFrame()
        for row in df.rows(named=True):
            if row["throwdata_avail"]:
                if type(rdf) is not ps.DataFrame:
                    rdf = DataLoader.calculate_stats_game(row)
                else:
                    rdf.extend(DataLoader.calculate_stats_game(row))
        return rdf

    def load_bowling_csv(path: str) -> ps.DataFrame:
        data = ps.read_csv(path, schema=DataLoader.ingest_schema)
        data = data.with_columns(
            ps.col("date").str.to_datetime("%m-%d-%Y").cast(ps.Date).alias("date"),
        )

        for frame_idx in range(1, 11):
            for throw_idx in range(1, 3 if frame_idx != 10 else 4):
                frame_col_name = f"f{frame_idx}_t{throw_idx}"
                data = data.with_columns(
                    ps.col(frame_col_name)
                    .map_elements(
                        lambda x: DataLoader.parse_throw(x),
                        return_dtype=DataLoader.throw_dtype,
                    )
                    .alias(frame_col_name)
                )

        stats_df = DataLoader.calculate_stats(data)

        return data, stats_df
