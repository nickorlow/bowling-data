# BART - The Bowling Analysis & Research Tool

The Bowling Analysis & Research Tool is a statically generated website that provides 
insight into the bowling performance of a group of bowlers given the frame-by-frame
scorecard data.

## Data Schema

See current data at `./backing-data/csv/`

- `bowler`: name of the bowler
- `date`: date game was played 
- `location`: where game was played (union: UT University Union, highland: Highland lanes)
- `game_num'`: number of game played in a day (1: first of the day, etc...) 
- `throwdata_avail`: a bool representing whether data for individual throws are avaliable
- `score`: player's score for given game
- `strike_cnt`: number of strikes player scored in a given game
- `spare_cnt`: number of spares player scored in a given game
- `foul_cnt`: number of fouls player had during a given game
- `fX_tY`: pins knocked down on throw Y of frame X. A value of `F` represents a foul. A blank value represents that that throw did not take place (usually due to a strike).
- `team`:  an optional affiliation with a team, not used for much other than cospetics presently
