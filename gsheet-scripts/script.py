from GSheetInterface import GSheetInterface
import pickle

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

team_inst_map = {}

def gen_name(team):
    name = ""
    name += team.name + "#"
    for member in team.members:
        name += member.handle + "#"
    return name

for team in Sheet.teams:
    team_inst_map[gen_name(team)] = team.institute

with open("team_map.pkl", 'wb') as file:
    pickle.dump(team_inst_map, file)
