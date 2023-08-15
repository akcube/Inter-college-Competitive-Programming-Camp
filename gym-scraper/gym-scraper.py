# Import stuff needed to make API calls
import requests
import json
import time
import datetime
import os

# Check if gym_list is available
if not os.path.isfile("gym_list.txt"):
    # API call to get gym contests
    gym_contests_req_url = "https://codeforces.com/api/contest.list?gym=true"

    # Make an API to get the list
    gym_contests_res = requests.request("GET", gym_contests_req_url)
    gym_contests_res = json.loads(gym_contests_res.text)

    # Check if the response is valid
    if gym_contests_res["status"] != "OK":
        # throw error and quit
        print("Error in first API call")
        print(gym_contests_res)
        quit()

    # Remove contests with difficulty < 4
    gym_contests = []
    for contest in gym_contests_res["result"]:
        try:
            if contest["difficulty"] >= 4 and contest['type'] == 'ICPC' and contest['durationSeconds'] == 18000:
                gym_contests.append(contest)
        except Exception as e:
            print("ERROR", e)
            pass

    # Put all the contests in gym_contests as 
    # comma separated value in gym_list.txt
    with open("gym_list.txt", "w") as f:
        for contest in gym_contests:
            f.write(str(contest["id"]) + ",")
        f.write("\n")

# Read the gym_list.txt file
with open("gym_list.txt", "r") as f:
    gym_list = f.read().split(",")
    gym_list = gym_list[:-1]

# Read the handles list from handles_list.txt
with open("handles_list.txt", "r") as f:
    handles_list = f.read().split("\n")
    handles_list = handles_list[:-1]

# Make the handles list semicolon separated
handles_list = ";".join(handles_list)

# URL to fetch the standings of a contest
standings_url = "https://codeforces.com/api/contest.standings?contestId={contest_id}&handles={handles_list}&from=1&count=40000&showUnofficial=true"

# Final contest IDs that are valid
final_list_contests = []

# Iterate over every contest ID
for contest_id in gym_list:
    # Avoiding timeout
    time.sleep(0.5)

    # Current request URL
    req_url = standings_url.format(contest_id=contest_id, handles_list=handles_list)

    # Make an API call to get the standings
    res = requests.request("GET", req_url)

    try:
        # Convert the response to JSON
        res = json.loads(res.text)

        # Check if the response is valid
        if res["status"] != "OK":
            # throw error and quit
            print("Error in second API call")
            print(res)
            continue

        # If the size of rows is 0 then 
        # noone submitted in this contest
        if len(res["result"]["rows"]) == 0:
            print(contest_id, res["result"]["contest"]["name"])
            final_list_contests.append((contest_id, res["result"]["contest"]["name"]))

    except Exception as e:
        print(e)
        pass

# Put the final list of contest IDs in a different file 
with open("final_list.txt", "w") as f:
    for contest_id, name in final_list_contests:
        f.write(str(contest_id) + ", " + name + "\n")
    f.write("\n")