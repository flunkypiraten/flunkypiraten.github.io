#!/usr/bin/env python3

import argparse
import copy
import re
from ruamel.yaml import YAML
from datetime import datetime, timedelta


def read_ranking_file(fn):
    data = fn.read()
    yaml = YAML()
    data = yaml.load(data)
    return data


def get_tournament(tname, data):
    for tnmt in data["tournaments"]:
        if tnmt["name"] == tname:
            return tnmt
    return None


def get_player(pname, ranking):
    for rank, player in enumerate(ranking, 1):
        if player["name"] == pname:
            return (rank, player)


def get_season_years():
    first_year = datetime.today().year if datetime.today().month in [10,11,12] else datetime.today().year - 1
    second_year = first_year + 1
    return first_year, second_year


def calc_ranking(data, day=None):
    tnmts = []
    if day is None:
        day = datetime.today()
    # get tournaments in rolling range
    for tnmt in data["tournaments"]:
        tday = datetime.strptime(tnmt["date"], "%d.%m.%Y")
        if (day - tday).days < 365 * data["rolling_range"] and (day - tday).days >= 0:
            tnmts.append(tnmt)
    for player in data["players"]:
        points = 0
        for tname, res in player["results"].items():
            if tname in [t["name"] for t in tnmts]:
                category = get_tournament(tname, data)["category"]
                points += data["points"][category][res]
        player["points"] = points
    ranking = copy.deepcopy(sorted(data["players"], key=lambda p: p["points"], reverse=True))
    return ranking


def calc_season_ranking(data, day=None):
    tnmts = []
    if day is None:
        day = datetime.today()
    # get tournaments in range
    for tnmt in data["tournaments"]:
        years =  get_season_years()
        cutoff = datetime(years[0], 10, 1, 0, 0)
        tday = datetime.strptime(tnmt["date"], "%d.%m.%Y")
        if (tday - cutoff).days >= 0 and (day - tday).days >= 0:
            tnmts.append(tnmt)
    for player in data["players"]:
        points = 0
        for tname, res in player["results"].items():
            if tname in [t["name"] for t in tnmts]:
                category = get_tournament(tname, data)["category"]
                points += data["points"][category][res]
        player["season_points"] = points
    ranking = copy.deepcopy(sorted(data["players"], key=lambda p: p["season_points"], reverse=True))
    return ranking


def get_table(data):
    rank_enhance = r'<span style="color: #008450">▲</span>'
    rank_degrade = r'<span style="color: #B81D13">▼</span>'
    rank_stay = r'<span style="color: #EFB700">-</span>'
    rank_new = r'&#x1F195;'
    header = (
        "| Rank | Player | All-time titles 🥇 | All-time 2nd 🥈 | "
        + "All-time 3rd 🥉 | Ranking points |\n"
        + "|------|------|------|------|------|------:|\n"
    )
    output = header
    last_tournament = datetime.strptime(
        sorted(list(data["tournaments"]), key=lambda t: datetime.strptime(t["date"], "%d.%m.%Y"))[
            -1
        ]["date"],
        "%d.%m.%Y",
    ) - timedelta(days=1)
    ranking_prev = calc_ranking(data, last_tournament)
    ranking_now = calc_ranking(data)
    prev_score = -1
    for rank, player in enumerate(ranking_now, 1):
        fullname = player["name"]
        if "alias" in player:
            fullname += " *formerly known as* "
            fullname += ", ".join(player["alias"])
        rank_change = r'<span style="font-size: small">('
        rank_prev, player_prev = get_player(player["name"], ranking_prev)
        if player_prev["points"] == 0:
            rank_change += rank_new
        elif rank_prev > rank:
            rank_change += rank_enhance + str(rank_prev - rank)
        elif rank_prev == rank:
            rank_change += rank_stay
        elif rank_prev < rank:
            rank_change += rank_degrade + str(rank_prev - rank)
        rank_change += r')</span>'
        cat_1_tournaments = [get_tournament(tournmnt, data)["name"] for tournmnt in player["results"].keys() if get_tournament(tournmnt, data)["category"] == 1]
        t_1st = [(t,r) for t,r in player["results"].items() if t in cat_1_tournaments and r == "1"]
        t_2nd = [(t,r) for t,r in player["results"].items() if t in cat_1_tournaments and r == "2"]
        t_3rd = [(t,r) for t,r in player["results"].items() if t in cat_1_tournaments and r == "3"]
        num_1s = len(t_1st)
        num_2s = len(t_2nd)
        num_3s = len(t_3rd) 
        if num_1s == 0:
            num_1s = ""
            names_1s = ""
        else:
            names_1s = [x[0] for x in t_1st]
            names_1s = sorted([int(get_tournament(x, data)["date"].split(".")[-1]) for x in names_1s])
            names_1s =  "(" + ", ".join([str(x) for x in names_1s]) + ")"
        if num_2s == 0:
            num_2s = ""
            names_2s = ""
        else:
            names_2s = [x[0] for x in t_2nd]
            names_2s = sorted([int(get_tournament(x, data)["date"].split(".")[-1]) for x in names_2s])
            names_2s =  "(" + ", ".join([str(x) for x in names_2s]) + ")"
        if num_3s == 0:
            num_3s = ""
            names_3s = ""
        else:
            names_3s = [x[0] for x in t_3rd]
            names_3s = sorted([int(get_tournament(x, data)["date"].split(".")[-1]) for x in names_3s])
            names_3s =  "(" + ", ".join([str(x) for x in names_3s]) + ")"
        line = "| {}{} | {} | {} {} | {} {} | {} {} | {} |\n".format(
            # str(rank) + " " if player["points"] != prev_score else "".join(["&nbsp;"] * (2 + len(str(rank)))),
            str(rank) + " " if player["points"] != prev_score else "&nbsp;&nbsp;&nbsp;",
            rank_change,
            fullname,
            num_1s,
            names_1s,
            num_2s,
            names_2s,
            num_3s,
            names_3s,
            player["points"],
        )
        output += line
        prev_score = player["points"]
    return output, last_tournament + timedelta(days=2)


def get_season_table(data):
    rank_enhance = r'<span style="color: #008450">▲</span>'
    rank_degrade = r'<span style="color: #B81D13">▼</span>'
    rank_stay = r'<span style="color: #EFB700">-</span>'
    rank_new = r'&#x1F195;'
    season = get_season_years()
    cutoff = datetime(season[0], 10, 1, 0, 0)
    header = (
        "| Rank | Player | Ranking points season {}/{}|\n".format(season[0], season[1])
        + "|------|--------|-------------------------------:|\n"
    )
    output = header
    last_tournament = datetime.strptime(
        sorted(list(data["tournaments"]), key=lambda t: datetime.strptime(t["date"], "%d.%m.%Y"))[
            -1
        ]["date"],
        "%d.%m.%Y",
    ) - timedelta(days=1)
    if (last_tournament - cutoff).days < 0:
        ranking_prev = calc_season_ranking(data, cutoff)
    else:
        ranking_prev = calc_season_ranking(data, last_tournament)
    ranking_now = calc_season_ranking(data)
    prev_score = -1
    for rank, player in enumerate(ranking_now, 1):
        if player["season_points"] == 0:
            continue
        fullname = player["name"]
        if "alias" in player:
            fullname += " *formerly known as* "
            fullname += ", ".join(player["alias"])
        rank_change = r'<span style="font-size: small">('
        rank_prev, player_prev = get_player(player["name"], ranking_prev)
        if player_prev["season_points"] == 0:
            rank_change += rank_new
        elif rank_prev > rank:
            rank_change += rank_enhance + str(rank_prev - rank)
        elif rank_prev == rank:
            rank_change += rank_stay
        elif rank_prev < rank:
            rank_change += rank_degrade + str(rank_prev - rank)
        rank_change += r')</span>'
        line = "| {}{} | {} | {} |\n".format(
            str(rank) + " " if player["season_points"] != prev_score else "&nbsp;&nbsp;&nbsp;",
            rank_change,
            fullname,
            player["season_points"],
        )
        output += line
        prev_score = player["season_points"]
    return output, last_tournament + timedelta(days=2)


def main():
    parser = argparse.ArgumentParser(
        description="Parser for evaluating the ranking YAML file."
    )
    parser.add_argument(
        "--input",
        "-i",
        nargs="?",
        type=argparse.FileType("r"),
        default="_data/alltimeranking.yaml",
        help="YAML file to import ranking from",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        default=False,
        help="Update ranking file for website",
    )
    parser.add_argument(
        "--update-season",
        "-s",
        action="store_true",
        default=False,
        help="Update season ranking for website",
    )
    args = parser.parse_args()
    data = read_ranking_file(args.input)
    if args.update:
        ranking_fn = "_pages/worldranking.md"
        table, cut_off = get_table(data)
        cut_off = datetime.strftime(cut_off, "%d.%m.%Y")
        with open(ranking_fn) as f:
            ranking_file = f.read()
        ranking_file = re.sub(r"_Cut-off date: .*", "_Cut-off date: {}_".format(cut_off), ranking_file)
        ranking_file_pre_table = ranking_file.split("<!-- table tag start -->\n\n")[0]
        ranking_file_post_table = ranking_file.split("\n\n<!-- table tag end -->")[-1]
        ranking_file = ranking_file_pre_table + "<!-- table tag start -->\n\n" + table + "\n\n<!-- table tag end -->" + ranking_file_post_table
        with open(ranking_fn, "w") as f:
            f.write(ranking_file)
    elif args.update_season:
        ranking_fn = "_pages/worldranking.md"
        table, cut_off = get_season_table(data)
        with open(ranking_fn) as f:
            ranking_file = f.read()
        ranking_file_pre_table = ranking_file.split("<!-- season_table tag start -->\n\n")[0]
        ranking_file_post_table = ranking_file.split("\n\n<!-- season_table tag end -->")[-1]
        ranking_file = ranking_file_pre_table + "<!-- season_table tag start -->\n\n" + table + "\n\n<!-- season_table tag end -->" + ranking_file_post_table
        with open(ranking_fn, "w") as f:
            f.write(ranking_file)
    else:
        ranking = calc_ranking(data)
        last_tournament = datetime.strptime(
            sorted(list(data["tournaments"]), key=lambda t: datetime.strptime(t["date"], "%d.%m.%Y"))[
                -1
            ]["date"],
            "%d.%m.%Y",
        ) - timedelta(days=1)
        ranking_prev = calc_ranking(data, last_tournament)

        for rank, player in enumerate(ranking, 1):
            fullname = player["name"]
            if "alias" in player:
                fullname += " formerly known as "
                fullname += ", ".join(player["alias"])
            change_str = "(" 
            rank_prev, player_prev = get_player(player["name"], ranking_prev)
            rank_change = str(abs(rank_prev - rank)) if rank_prev - rank != 0 else ""
            if rank_prev > rank:
                change_str += "▲" + rank_change + ")"
            elif rank_prev == rank:
                change_str += "-" + rank_change + ")"
            elif rank_prev < rank:
                change_str += "▼" + rank_change + ")"
            else:
                change_str = ""
            print("{:>2} {:>4} {:<30} {:>5}".format(rank, change_str, fullname, player["points"]))


if __name__ == "__main__":
    main()
