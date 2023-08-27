from GSheetInterface import GSheetInterface
import os
import shutil

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

data_directory = "mailing-list/"
if os.path.exists(data_directory):
    shutil.rmtree(data_directory)
os.makedirs("mailing-list", exist_ok=True)

files = {}
for team in Sheet.teams:
    if team.institute in files:
        f = files[team.institute]
    else:
        f = files[team.institute] = open(os.path.join(data_directory, team.institute + ".csv"), "w")
    f.write(','.join(team.emails) + ',')
