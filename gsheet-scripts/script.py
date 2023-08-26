from GSheetInterface import GSheetInterface

Sheet = GSheetInterface(keyfile='../secrets/icpc-camp-service-account-creds.json',
                        spreadsheet_title='Inter-College Competitive Programming Camp Registration (Responses)',
                        cache_file='cache.pkl')