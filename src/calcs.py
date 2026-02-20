import polars as ps
import numpy as np

class Calculations:
    def __init__(self, throws_df: ps.DataFrame, games_df: ps.DataFrame):
        self.throws_df = throws_df
        self.games_df = games_df
        self.individual_games = Calculations.get_individual_games(games_df)
        self.wins_matrix = self.create_wins_matrix(games_df)
        self.stats = self.get_bowler_stats(games_df)
        self.frames_df = Calculations.get_frames(games_df) 
        self.fills_df =  self.get_fill_rates(games_df) 
        self.pinfall_df =  self.get_pe_df(games_df) 

    def create_wins_matrix(self, df, floor_losses=False) -> ps.DataFrame:
        wins_matrix = ps.DataFrame()
        h2h_df = (df.join(df, on=["game_num","location","date"], how="inner")
                    .with_columns(
                        (ps.col("score") > ps.col("score_right")).alias("won"),
                        (ps.col("score") < ps.col("score_right")).alias("lost")
                    )
                    .group_by(["bowler","bowler_right"])
                    .agg(
                        ps.col("won").sum().cast(ps.Int32),
                        ps.col("lost").sum().cast(ps.Int32)
                    ))
        h2h_df =  (h2h_df.with_columns(
                        (ps.col("lost") - ps.col("won")).alias("net_wins")
                    ))
        if  floor_losses:
            h2h_df = (h2h_df.with_columns(
                        ps.when(ps.col("net_wins") < 0).then(0).otherwise(ps.col("net_wins")).alias("net_wins")
                ))
        h2h_df = (h2h_df.pivot("bowler_right", index="bowler", values="net_wins")
                    .sort("bowler")
                  )
        h2h_df = h2h_df.select(["bowler"] + sorted(h2h_df.columns[1:]))
        return h2h_df

    def split_tenth_frame(bowlers, first_throw, second_throw, bowler_name, row):
        # Special case for frame 10, since we have 3 compile
        # 1 - no spare, 2 throws treated as normal
        # 2 - spare in first 2 throws, 3rd throw granted
        # 3 - strike in first throw, pins reset for 2nd, 3rd throw granted
        #     if we get a second strike, pins will be reset

        # We'll handle these cases as:
        # 1 - treat normally
        # 2 - 1st 2 throws treated normally, 3rd added as first throw
        # 3 - new throw created per each strike
        t1 = row[f"f10_t1"]["pins_hit"]
        t2 = row[f"f10_t2"]["pins_hit"]

        # case 1/2
        if t1 != 10:
            bowlers.append(bowler_name)
            first_throw.append(t1)
            second_throw.append(t2)
        else:
            # case 3
            # first throw strike
            bowlers.append(bowler_name)
            first_throw.append(t1)
            second_throw.append(0)

            t3 = row[f"f10_t3"]["pins_hit"]

            # second throw not strike
            if t2 != 10:
                bowlers.append(bowler_name)
                first_throw.append(t2)
                second_throw.append(t3)
            else:
                # second throw not strike
                bowlers.append(bowler_name)
                first_throw.append(t2)
                second_throw.append(0)
                bowlers.append(bowler_name)
                first_throw.append(t3)
                second_throw.append(0)

    def get_frames(df) -> ps.DataFrame:
        bowlers, first_throw, second_throw = [], [], []

        for row in df.rows(named=True):
            bowler_name = row["bowler"]
            if row["throwdata_avail"]:
                for frame_idx in range(1, 10):
                    bowlers.append(bowler_name)
                    first_throw.append(row[f"f{frame_idx}_t1"]["pins_hit"])
                    if row[f"f{frame_idx}_t1"]["pins_hit"] != 10:
                        second_throw.append(row[f"f{frame_idx}_t2"]["pins_hit"])
                    else:
                        second_throw.append(None)
                Calculations.split_tenth_frame(
                    bowlers, first_throw, second_throw, bowler_name, row
                )

        return ps.DataFrame({"t1": first_throw, "t2": second_throw, "bowler": bowlers})

    def _calculate_average_row(self, long_format_df, group_col="t1"):
        positives_df = long_format_df.group_by(group_col).agg(
            ps.col("val").struct.field("positives").sum().cast(ps.UInt32).alias("positives"),
        )
        
        sample_size_df = long_format_df.group_by([group_col, "bowler"]).agg(
            ps.col("val").struct.field("sample_size").first().cast(ps.UInt32).alias("sample_size"),
        ).group_by(group_col).agg(
            ps.col("sample_size").sum().cast(ps.UInt32).alias("sample_size"),
        )
        
        avg_df = positives_df.join(sample_size_df, on=group_col, how="inner")
        
        avg_df = avg_df.with_columns(
            ps.struct(
                ps.col("positives").alias("positives"),
                ps.col("sample_size").alias("sample_size"),
                (ps.col("positives")/ps.col("sample_size")*100).round(2).alias("pct")
            ).alias("val")
        ).with_columns(
            ps.lit("average").alias("bowler")
        ).select(["bowler", "val", group_col])
        
        return avg_df

    def get_pe_df(self, full_data):
        all_throws_df = self.frames_df 

        pe_df = (all_throws_df.with_columns().group_by(["t1","bowler"]).agg(
                ps.col("t1").count().cast(ps.UInt32).alias("hit_cnt"),
            ))
        pe_df2 = (all_throws_df.group_by("bowler").agg(ps.col("t1").count().cast(ps.UInt32).alias("attempt_cnt")))
        pe_df = (pe_df.join(pe_df2, on="bowler", how="inner")
            .with_columns(
                ps.struct(
                    (ps.col("hit_cnt")).alias("positives"),
                    (ps.col("attempt_cnt")).alias("sample_size"),
                    (ps.col("hit_cnt")/ps.col("attempt_cnt")*100).round(2).alias("pct")
                ).alias("val")
            ).select(["bowler","val", "t1"]))
        
        avg_df = self._calculate_average_row(pe_df, group_col="t1")
        
        pe_df = ps.concat([pe_df, avg_df])
        
        pe_df = pe_df.pivot("t1",index="bowler",values="val")
        pe_df = pe_df.select(["bowler"] + [str(y) for y in sorted([int(x) for x in pe_df.columns[1:]])])
        
        avg_row = pe_df.filter(ps.col("bowler") == "average")
        bowler_rows = pe_df.filter(ps.col("bowler") != "average").sort("bowler")
        pe_df = ps.concat([bowler_rows, avg_row])
        
        return pe_df

    def get_fill_rates(self, full_data):
        all_throws_df = self.frames_df 

        pe_df = (all_throws_df.group_by(["t1","bowler"]).agg(
                ((ps.col("t2") + ps.col("t1")) == 10).sum().alias("spare_cnt"),
                ps.col("t1").count().alias("attempt_cnt"),
            )
            .filter(ps.col("t1") != 10)
            .with_columns(
                ps.struct(
                    (ps.col("spare_cnt")).alias("positives"),
                    (ps.col("attempt_cnt")).alias("sample_size"),
                    (ps.col("spare_cnt")/ps.col("attempt_cnt")*100).round(2).alias("pct")
                ).alias("val")
            ).select(["bowler","val", "t1"]))
        
        avg_df = self._calculate_average_row(pe_df, group_col="t1")
        
        pe_df = ps.concat([pe_df, avg_df])
        
        pe_df = pe_df.pivot("t1",index="bowler",values="val")
        pe_df = pe_df.select(["bowler"]+sorted(pe_df.columns[1:]))
        
        avg_row = pe_df.filter(ps.col("bowler") == "average")
        bowler_rows = pe_df.filter(ps.col("bowler") != "average").sort("bowler")
        pe_df = ps.concat([bowler_rows, avg_row])
        
        return pe_df

    def get_individual_games(df) -> ps.DataFrame:
        return (
            df.select(["date", "location", "game_num", "bowler", "score"])
            .group_by(["date", "location", "game_num"])
            .agg(ps.col("bowler").get(ps.col("score").arg_max()).alias("winner"))
            .sort(["date", "game_num"], descending=True)
        )

    def get_page_ranks(self, stats_df):
        win_matrix = self.create_wins_matrix(self.games_df,  True)
        extended_avgs = (stats_df.select(["avg_last_8"])
                        .transpose(column_names=stats_df["bowler"])
                        .select(sorted(stats_df["bowler"])))
        bowlers = win_matrix['bowler']
        win_matrix = win_matrix.drop("bowler").fill_null(0)
        pr_df = ps.from_numpy(np.dot(extended_avgs, win_matrix))
        pr_df.columns = bowlers
        return pr_df

    def get_bowler_stats(self, df) -> ps.DataFrame:
        win_counts = self.individual_games.group_by("winner").count()
        stats_df = (
            df.sort("score")
            .group_by("bowler")
            .agg(
                ps.col("score").last().alias("high_score"),
                ps.col("score").top_k_by(k=8, by="date").mean().alias("avg_last_8"),
                ps.col("score").top_k_by(k=8, by="date").count().alias("num_ranked_games"),
                ps.col("score").mean().alias("avg_score").round(2),
                ps.col("strike_cnt").sum().alias("total_strikes"),
                ps.col("spare_cnt").sum().alias("total_spares"),
                ps.col("team").last().alias("team"),
                ps.col("score").top_k_by(k=8, by="date").std().alias("std"),
                ps.col("score").count().alias("num_games"),
            )
            .sort("bowler")
            .join(win_counts, how="left", left_on="bowler", right_on="winner")
            .rename({"count": "total_wins"})
            .with_columns(
                (1.96 * (ps.col("std") / ps.col("num_ranked_games").sqrt())).alias(
                    "conf_int_95%"
                ),
            )
            .with_columns(
                ps.col("avg_last_8").round(2),
                ps.col("conf_int_95%").round(2),
                ps.col("std").round(2),
                (ps.col("avg_last_8") - ps.col("conf_int_95%"))
                .round(2)
                .alias("ci_lower_bound"),
                (ps.col("avg_last_8") + ps.col("conf_int_95%"))
                .round(2)
                .alias("ci_upper_bound"),
                ps.col("total_wins").fill_null(0),
            )
        )

        return (
            stats_df.with_columns(
                ps.Series("page_rank",  self.get_page_ranks(stats_df).transpose()).round(0)
            )
            .select(
                [
                    "bowler",
                    "avg_last_8",
                    "std",
                    "conf_int_95%",
                    "ci_lower_bound",
                    "ci_upper_bound",
                    "high_score",
                    "total_strikes",
                    "total_spares",
                    "num_games",
                    "total_wins",
                    "avg_score",
                    "page_rank",
                    "team",
                ]
            )
            .sort("avg_score", descending=True)
        )

    def highest_scores(self) -> ps.DataFrame:
        return self.games_df.sort("score", descending=True).limit(10).select(["bowler", "score"])
