import gspread
from oauth2client.service_account import ServiceAccountCredentials
from enum import StrEnum
from dataclasses import dataclass
import cfutils.api as cf
import pickle
import os


class FormHeaders(StrEnum):
    TEAM = "Team Name"
    INSTITUTE = "Institute"
    ALTS_CSV = "Comma separated list of accounts used by members to give Gym contests on CF"
    NAME = "Name"
    HANDLE = "CF Handle"
    EMAIL = "Institute Email"
    PHONE = "Phone number"
    DISCORD = "Discord handle (Recommended)"


@dataclass
class Member:
    handle: str
    name: str
    email: str


@dataclass
class Team:
    name: str
    institute: str
    members: list[Member]
    alts: list[str]


class GSheetInterface:
    """Class for interacting with Google Sheets and handling teams data."""

    def __init__(self, keyfile: str, spreadsheet_title: str, cache_file: str = None):
        """
        Initialize the GSheetInterface.
        Args:
            keyfile (str): Path to the Google Sheets keyfile.
            spreadsheet_title (str): Title of the Google Sheets spreadsheet.
            cache_file (str): Optional. Path to the cache file for storing data.

        """
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, self.scope)
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet = self.client.open(spreadsheet_title).get_worksheet(0)
        self.headers = []
        self.teams = []
        self.error_logs = []

        if cache_file is None or not os.path.exists(cache_file):
            self.__fetch__(cache_file)
        else:
            self.__load__(cache_file)

    def construct_team(self, team_dict: dict) -> Team:
        """
        Construct a Team object from a dictionary.
        Args:
            team_dict (dict): Dictionary containing team information.
        Returns:
            Team: The constructed Team object.
        Raises:
            InvalidTeamError: If the team information is invalid.
        """
        log = []
        required_fields = [FormHeaders.TEAM, FormHeaders.INSTITUTE, FormHeaders.NAME, FormHeaders.EMAIL,
                           FormHeaders.HANDLE]

        if not all(team_dict[field] for field in required_fields):
            log.append("Required arguments not provided")

        if not (len(team_dict[FormHeaders.NAME]) == len(team_dict[FormHeaders.HANDLE]) == len(
                team_dict[FormHeaders.EMAIL])):
            log.append("Mismatch in the number of required fields provided")

        for handle in team_dict[FormHeaders.HANDLE]:
            try:
                cf.User_Info(handles=[handle]).get(auth=False)
            except cf.CFAPIError as e:
                log.append(e.__str__())

        if not log:
            members = [Member(handle=team_dict[FormHeaders.HANDLE][i],
                              name=team_dict[FormHeaders.NAME][i],
                              email=team_dict[FormHeaders.EMAIL][i])
                       for i in range(len(team_dict[FormHeaders.NAME]))]
            return Team(name=team_dict[FormHeaders.TEAM][0],
                        institute=team_dict[FormHeaders.INSTITUTE][0],
                        members=members,
                        alts=[alt.strip() for alt in team_dict[FormHeaders.ALTS_CSV][0].split(",")] if team_dict[
                            FormHeaders.ALTS_CSV] else [])
        else:
            self.error_logs.append((team_dict[FormHeaders.TEAM][0], log))
            raise InvalidTeamError("Invalid details given. Errors: {errors}".format(errors=", ".join(log)))

    def __fetch__(self, cache_file: str):
        """Fetch data from Google Sheets and populate teams and error_logs."""
        data = self.spreadsheet.get_all_values()
        self.headers = [column_name.strip() for column_name in data[0]]
        num_teams = len(data) - 1

        for team_id, row in enumerate(data[1:]):
            print("Processing team {id}/{num_teams}".format(id=team_id + 1, num_teams=num_teams))
            team_dict = {column_name: [] for column_name in self.headers}

            for i, column_value in enumerate(row):
                if column_value.strip():
                    team_dict[self.headers[i]].append(column_value.strip())

            try:
                self.teams.append(self.construct_team(team_dict))
            except InvalidTeamError:
                pass
            print("Errors logged: {num_errors}\n".format(num_errors=len(self.error_logs)))

        if cache_file is not None and os.path.exists(cache_file):
            with open(cache_file, 'wb') as dump_file:
                pickle.dump(self.teams, dump_file)
                pickle.dump(self.error_logs, dump_file)

    def __load__(self, cache_file: str):
        """Load data from the cache file."""
        with open(cache_file, 'rb') as dump_file:
            self.teams = pickle.load(dump_file)
            self.error_logs = pickle.load(dump_file)

    def get_all_handles(self) -> set:
        """Get all CF handles from the teams and alts."""
        cf_handles_set = set()
        for team in self.teams:
            for member in team.members:
                cf_handles_set.update(member.handle)
            cf_handles_set.update(team.alts)
        return cf_handles_set


class InvalidTeamError(Exception):
    """Custom exception class for invalid team information."""
    pass
