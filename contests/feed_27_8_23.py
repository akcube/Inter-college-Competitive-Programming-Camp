import os
import sys
import logging
import click
import pickle
from dotenv import load_dotenv

import cfutils.api as cf
from cfutils.icpctools.feed_generator import (
    CFContestConfig,
    EventFeedFromCFContest,
    ContestTeam,
)


### GLOBAL, DO NOT EDIT HERE
team_map: dict[str, str] = {}


def hashTeam(teamName: str, members: list[str]) -> str:
    """Must sort user names to make the hash permutation invariant!"""
    name = teamName + "#"
    members = sorted(members)
    for member in members:
        name += member + "#"
    return name


class MyConfig(CFContestConfig):
    def getRegion(self, team: ContestTeam) -> str:
        name = hashTeam(team.name, [u.handle for u in team.party.members])
        if name in team_map:
            return team_map[name]
        else:
            return self.regions[0]  # default region


def cli():
    """
    Usage: python feed_27_8_23.py
    """

    # <config>
    contest_id = 496804
    status_file = "./status.json"
    standings_file = "./standings.json"
    feed_file = "./feed.json"
    auth = True
    asManager = True
    unofficial = False

    teams_pickle = "../gsheet-scripts/team_map.pkl"
    # remove ranklist teams that are NOT in the gsheets pickle.
    remove_unregistered_teams = False
    # </config>

    with open(teams_pickle, "rb") as inf:
        raw_team_map = pickle.load(inf)

    for name, org in raw_team_map.items():
        words = name.split("#")[:-1]
        team = words[0]
        members = words[1:]

        name_fixed = hashTeam(team, members)
        team_map[name_fixed] = org

    org_list: list[str] = list(set(raw_team_map.values()))

    # load API keys if neccessary
    if auth:
        assert load_dotenv()
        assert os.getenv("CODEFORCES_API_KEY") is not None
        assert os.getenv("CODEFORCES_API_SECRET") is not None

    # get contest data from codeforces
    submissions: list[cf.Submission] = cf.Contest_Status(
        asManager=asManager, contestId=contest_id, From=1, count=25000
    ).get(auth=auth, output_file=status_file, load_from_file=status_file)

    standings: cf.Contest_Standings.Result = cf.Contest_Standings(
        asManager=asManager,
        contestId=contest_id,
        From=1,
        count=10000,
        showUnofficial=unofficial,
    ).get(auth=auth, output_file=standings_file, load_from_file=standings_file)

    # generate the event feed
    feedGen = EventFeedFromCFContest(
        config=MyConfig(
            freezeDurationSeconds=60 * 60,
            # first value is the default (fallback) region
            regions=["Other"] + org_list,
            include_virtual=unofficial,
            include_out_of_comp=unofficial,
        )
    )

    ranklist = standings.rows
    if remove_unregistered_teams:
        # filter out unregistered teams?
        logging.info("Removing unregistered teams...")
        team_count_init = len(ranklist)
        ranklist = [
            row
            for row in standings.rows
            if row.party.teamName is not None
            and hashTeam(row.party.teamName, [u.handle for u in row.party.members])
            in team_map
        ]
        team_count_final = len(ranklist)
        logging.info(
            "Final #teams: %d (initially %d)", team_count_final, team_count_init
        )

    feed = feedGen.generate(
        contest=standings.contest,
        problems=standings.problems,
        ranklist=ranklist,
        submissions=submissions,
    )

    with open(feed_file, "w") as outf:
        for event in feed:
            outf.write(event)
            outf.write("\n")
    logging.info(f"Contest {standings.contest.id} feed generated! Wrote to {feed_file}")


if __name__ == "__main__":
    verbose = False
    logging.basicConfig(
        format="[%(levelname)s]: %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )

    cli()  # type: ignore
