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


try:
    assert (len(sys.argv) == 2)
    assert (int(sys.argv[1]) >= 0)
    if not load_dotenv():
        raise LoadDotenvError("Failed to load environment variables. Did you provide the .env file?")
    if os.getenv(Keys.CODEFORCES_API_KEY.name) is None or os.getenv(Keys.CODEFORCES_API_SECRET.name) is None:
        raise MissingEnvironmentVariableError(
            "{api_key} or {api_secret} environment variables not set.".format(api_key=Keys.CODEFORCES_API_KEY.name,
                                                                              api_secret=Keys.CODEFORCES_API_SECRET.name))
    Result = cf.Contest_Standings(contestId=int(sys.argv[1]),
                                  From=1,
                                  count=40000,
                                  asManager=False,
                                  showUnofficial=False).get(auth=True)
    contest, problems, rows = Result.contest, Result.problems, Result.rows
    print("Contest identified: {contest_name}\nGenerating table now...".format(contest_name=contest.name))
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

headers = ["#", "Team", "Representing", "Rating", "=", "Penalty"] + [p.index for p in problems]
ranklist = []

def get_institute(party):
    for t in teams[party.teamName.lower()]:
        m1 = set([m.handle.lower() for m in t.members])
        m2 = set([m.handle.lower() for m in party.members])
        if len(m1.intersection(m2)) > 0:
            return t.institute
    return None

rows = [row for row in rows if row.party.teamName is not None and get_institute(row.party) is not None]
max_solved = max(row.points for row in rows)

institute_champions = {}
first_solves = {}
first_solves_team = {}


def apply_tag(s, tag, params={}):
    s = round(s, 2) if isinstance(s, float) else s
    return '<' + tag + " " + " ".join(op + '=' + '\"' + arg + '\"' for op, arg in params.items()) + '>' + str(
        s) + '</' + tag + '>'


def center(s):
    return apply_tag(s, 'center')


def bold(s):
    return apply_tag(s, 'b')

group_rank = 1
for row in rows:

    def get_rank(rank):
        if rank <= 4:
            return apply_tag("GOLD {rank}".format(rank=rank), "span", {'class': 'label label-gold'})
        elif rank <= 8:
            return apply_tag("SILVER {rank}".format(rank=rank), "span", {'class': 'label label-silver'})
        elif rank <= 12:
            return apply_tag("BRONZE {rank}".format(rank=rank), "span", {'class': 'label label-bronze'})
        else:
            return str(rank)


    def get_rating(rank):
        n = max(50, len(rows))
        return 3000 * ((n - rank + 1) / n) * (row.points / max_solved)


    def get_team(row):
        res = apply_tag(row.party.teamName, 'span', {'class': 'team-name'}) + ": "
        return res + ", ".join([member.handle for member in row.party.members])


    def generate_cell(result):
        cell = "+" if result.points > 0 else ""
        cell = "-" if result.points == 0 and result.rejectedAttemptCount > 0 else cell
        if not cell:
            return cell
        cell += '' if not result.rejectedAttemptCount else str(result.rejectedAttemptCount)
        if not cell.startswith('+'):
            return apply_tag(cell, "span", {'class': 'problem-wa'})
        cell = apply_tag(cell, "span", {'class': 'problem-ac'})
        cell += '<br>' + str(datetime.timedelta(seconds=result.bestSubmissionTimeSeconds))
        return cell


    if row.party.teamName is None:
        continue
    
    institute = get_institute(row.party)
    
    if institute is None:
        continue

    entry = [center(get_rank(group_rank)),
             get_team(row),
             center(institute),
             center(bold(get_rating(group_rank))),
             center(int(row.points)),
             center(row.penalty)]
    entry += [center(generate_cell(result)) for result in row.problemResults]
    ranklist.append(entry)

    if institute not in institute_champions:
        institute_champions[institute] = row.party.teamName

    for id, res in enumerate(row.problemResults):
        if res.points == 0:
            continue
        pid = problems[id].index
        if pid not in first_solves or first_solves[pid] > res.bestSubmissionTimeSeconds:
            first_solves[pid] = res.bestSubmissionTimeSeconds
            first_solves_team[pid] = row.party.teamName
    group_rank += 1

institute_champions_table = []
for institute, team in institute_champions.items():
    institute = center(institute)
    team = center(apply_tag(team, 'span', {'class': 'team-name'}))
    institute_champions_table.append([institute, team])

first_solves_table = []
for problem, solve_time in first_solves.items():
    team = center(apply_tag(first_solves_team[problem], 'span', {'class': 'team-name'}))
    problem = center(problem)
    solve_time = center(str(datetime.timedelta(seconds=solve_time)))
    first_solves_table.append([problem, solve_time, team])


with open(contest.name.replace(' ', '-'), 'w') as outf:
    outf.write("# Awards\n\n## Regional Champions\n\n")
    outf.write(tabulate(institute_champions_table, headers=["Region", "Team"], tablefmt='github'))
    outf.write('\n\n## First Solves\n\n')
    outf.write(tabulate(first_solves_table, headers=["Problem", "Solve Time", "Team"], tablefmt='github'))
    outf.write('\n\n# Ranklist\n\n')
    outf.write(tabulate(ranklist, headers=headers, tablefmt='github'))
