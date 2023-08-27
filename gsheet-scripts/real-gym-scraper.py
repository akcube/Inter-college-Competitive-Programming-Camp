from GSheetInterface import GSheetInterface
import cfutils.api as cf
import os

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

cf_handles = set()
for team in Sheet.teams:
    for member in team.members:
        cf_handles.add(member.handle)
    cf_handles.update(team.alts)

contests_cache = 'cache/gym_contests.txt'
os.makedirs(os.path.dirname(contests_cache), exist_ok=True)
contests = cf.Contest_List(gym=True).get(output_file=contests_cache, load_from_file=contests_cache)

valid_gyms = []
num_contests = len(contests)
for num_contest, contest in enumerate(contests):
    print(f"Processing {num_contest} / {num_contests}")
    if contest.type != cf.ContestType.ICPC or contest.durationSeconds != 18000 or contest.difficulty is None or \
            contest.difficulty < 4:
        continue
    standings = cf.Contest_Standings(contestId=contest.id, From=1, count=40000, asManager=True, showUnofficial=True)\
        .get(auth=True)
    valid = True
    for row in standings.rows:
        for member in row.party.members:
            if member.handle in cf_handles:
                valid = False
                break
        if not valid:
            break
    if valid:
        valid_gyms.append((contest.id, contest.name))
        print(valid_gyms[-1])

print(valid_gyms)

with open("valid-gyms.txt", "w") as outf:
    for tup in valid_gyms:
        outf.write(tup.__str__() + "\n")