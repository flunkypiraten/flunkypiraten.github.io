#!/usr/bin/env python3

from ruamel.yaml import YAML
from datetime import datetime


def read_ranking_file(fn):
    with open(fn) as f:
        data = f.read()
    yaml = YAML()
    data = yaml.load(data)
    return data


def get_tournament(tname, data):
    for tnmt in data["tournaments"]:
        if tnmt["name"] == tname:
            return tnmt
    return None


def calc_ranking(data):
    tnmts = []
    today = datetime.today()
    # get tournaments in rolling range
    for tnmt in data["tournaments"]:
        tday = datetime.strptime(tnmt["date"], "%d.%m.%Y")
        if (today - tday).days < 365 * data["rolling_range"]:
            tnmts.append(tnmt)
    for player in data["players"]:
        points = 0
        for tname, res in player["results"].items():
            if tname in [t["name"] for t in tnmts]:
                category = get_tournament(tname, data)["category"]
                points += data["points"][category][res]
        player["points"] = points
    ranking = sorted(data["players"], key=lambda p: p["points"], reverse=True)
    return ranking


def main():
    fn = "_data/alltimeranking.yaml"
    data = read_ranking_file(fn)
    ranking = calc_ranking(data)
    for rank,player in enumerate(ranking, 1):
        fullname = player["name"]
        if "alias" in player:
            fullname += " formerly known as "
            fullname += ", ".join(player["alias"])
        print("{:>2} {:<30} {:>5}".format(rank, fullname, player["points"]))


if __name__ == "__main__":
    main()
