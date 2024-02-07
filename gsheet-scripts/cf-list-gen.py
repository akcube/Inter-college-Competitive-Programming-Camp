import cfutils.api as cf
from GSheetInterface import GSheetInterface

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

lst = []
unknown = []
num_teams = len(Sheet.teams)
for i, team in enumerate(Sheet.teams):
    handle = team.members[0].handle
    if handle in Sheet.rated_handles:
        lst.append((Sheet.rated_handles[handle].maxRating, handle))
    else:
        unknown.append(handle)
    print(f"Processed {i}/{num_teams}")

exp_delay = 1
while True:
    try:
        users = cf.User_Info(handles=unknown).get(delay=0.5)
        for user in users:
            lst.append((user.maxRating, user.handle))
        break
    except Exception as e:
        print("Error: {error}, retrying...".format(error=e.__str__()))
        exp_delay = min(exp_delay * 2, 30)
        continue


def custom_key(item):
    if item[0] is None:
        return 0
    else:
        return item[0]


sorted_data = sorted(lst, key=custom_key, reverse=True)
with open("cf-list.txt", 'w') as outfile:
    for rating, handle in sorted_data:
        outfile.write(handle + '\n')
