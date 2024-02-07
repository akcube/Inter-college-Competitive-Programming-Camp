import sys
from dotenv import load_dotenv
import os
import cfutils.api as cf
from enum import Enum
from GSheetInterface import GSheetInterface
from collections import defaultdict
from tabulate import tabulate
import datetime


class LoadDotenvError(Exception):
    pass


class MissingEnvironmentVariableError(Exception):
    pass


class Keys(Enum):
    CODEFORCES_API_KEY = "CODEFORCES_API_KEY"
    CODEFORCES_API_SECRET = "CODEFORCES_API_SECRET"

contests_list = [470038, 1866, 472462, 473814, 476508, 479592, 481471, 484403, 496804]
contest_data = []

for contest_id in contests_list:
    try:
        if not load_dotenv():
            raise LoadDotenvError("Failed to load environment variables. Did you provide the .env file?")
        if os.getenv(Keys.CODEFORCES_API_KEY.name) is None or os.getenv(Keys.CODEFORCES_API_SECRET.name) is None:
            raise MissingEnvironmentVariableError(
                "{api_key} or {api_secret} environment variables not set.".format(api_key=Keys.CODEFORCES_API_KEY.name,
                                                                                  api_secret=Keys.CODEFORCES_API_SECRET.name))
        Result = cf.Contest_Standings(contestId=contest_id,
                                      From=1,
                                      count=40000,
                                      asManager=False,
                                      showUnofficial=False).get(auth=True)
        contest, problems, rows = Result.contest, Result.problems, Result.rows
        print("Contest identified: {contest_name}\n".format(contest_name=contest.name))
        contest_data.append(rows)
    except (AssertionError, ValueError) as e:
        print("Error: Invalid usage, valid contest ID not provided.")
        print("Usage: python {file_name} <contest_id>".format(file_name=sys.argv[0]))
        exit(1)
    except cf.CFAPIError as e:
        print("Contest with ID: {contest_id} does not exist!".format(contest_id=int(sys.argv[1])))
        print(e)
        exit(1)
    except (LoadDotenvError, MissingEnvironmentVariableError) as e:
        print(e.__str__())
        exit(1)

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

'''
GSheet has team_name and handles. Can generate unique key thanks to unique handles (till end of year).
Let's make map of team_name to list of list of teams. Should be enough to uniquely determine everything.
'''

teams = defaultdict(list)
for team in Sheet.teams:
    teams[team.name.lower()].append(team)

def get_institute(party):
    for t in teams[party.teamName.lower()]:
        m1 = set([m.handle.lower() for m in t.members])
        m2 = set([m.handle.lower() for m in party.members])
        if len(m1.intersection(m2)) > 0:
            return t.institute
    return None

team_ratings = defaultdict(list)
for rows in contest_data:
    rows = [row for row in rows if row.party.teamName is not None and get_institute(row.party) is not None]
    max_solved = max(row.points for row in rows)

    group_rank = 1
    for row in rows:
        def get_rating(rank):
            n = max(50, len(rows))
            return 3000 * ((n - rank + 1) / n) * (row.points / max_solved)

        def get_team(party):
            for t in teams[party.teamName.lower()]:
                m1 = set([m.handle.lower() for m in t.members])
                m2 = set([m.handle.lower() for m in party.members])
                if len(m1.intersection(m2)) > 0:
                    return t
            return None

        if row.party.teamName is None or get_institute(row.party) is None:
            continue
        team_ratings[get_team(row.party)].append(get_rating(group_rank))
        group_rank += 1

MIN_CONTESTS = 5
disq_ratings = {key: value for key, value in team_ratings.items() if len(value) < MIN_CONTESTS}
team_ratings = {key: value for key, value in team_ratings.items() if len(value) >= MIN_CONTESTS}

def compute_out(team_ratings):
    out = []
    for team, ratings in team_ratings.items():
        ratings = sorted(ratings, reverse=True)[0:MIN_CONTESTS]
        final_rating = sum(ratings) / len(ratings)
        out.append((team, final_rating))
    out = sorted(out, key=lambda x: x[1], reverse=True)
    return out

qual_out = compute_out(team_ratings)
disq_out = compute_out(disq_ratings)

def print_out(out):
    for team, rating in out:
        print("Team: {}".format(team.name))
        print("Institute: {}".format(team.institute))
        print("Members: {}".format(", ".join([member.handle for member in team.members])))
        print("Rating: {}".format(rating))
        print("")

print("QUALIFIED TEAMS")
print_out(qual_out)

print("DISQUALIFIED TEAMS")
print_out(disq_out)