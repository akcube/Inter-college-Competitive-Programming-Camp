from GSheetInterface import GSheetInterface

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)')

cf_handles = set()
for team in Sheet.teams:
    if team.institute != 'LNMIIT':
        continue
    for member in team.members:
        cf_handles.add(member.handle)
    cf_handles.update(team.alts)

for handle in cf_handles:
    print(handle)
