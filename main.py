import os
from datetime import datetime, timedelta
from typing import NamedTuple
from zoneinfo import ZoneInfo

import requests
from todoist_api_python.api import TodoistAPI

IRAN_TZ = ZoneInfo("Asia/Tehran")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
TEAM_ID = 81  # FC Barcelona
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")


class MatchInfo(NamedTuple):
    match_dt: datetime
    opponent: str
    competition: str


def get_next_barca_match_info():
    url = f"https://api.football-data.org/v4/teams/{TEAM_ID}/matches?status=SCHEDULED&limit=1"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}

    res = requests.get(url, headers=headers)
    res.raise_for_status()
    match = res.json()["matches"][0]

    utc_dt = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
    iran_dt = utc_dt.astimezone(IRAN_TZ)
    opponent = match["awayTeam"]["name"] if match["homeTeam"]["id"] == TEAM_ID else match["homeTeam"]["name"]
    competition = match["competition"]["name"]
    return MatchInfo(match_dt=iran_dt, opponent=opponent, competition=competition)


def does_barca_plays_today() -> tuple[bool, MatchInfo]:
    next_match_info = get_next_barca_match_info()
    today_dt = datetime.now(IRAN_TZ)
    if next_match_info.match_dt.date() == today_dt.date():
        return True, next_match_info
    return False, next_match_info


def send_notification(text: str) -> None:
    response = requests.post("https://ntfy.sh/nattagh",
                             data=text.encode(encoding="utf-8"))

    response.raise_for_status()


def set_todoist(text: str, match_info: MatchInfo) -> None:
    api = TodoistAPI(TODOIST_API_KEY)
    notif_time = match_info.match_dt - timedelta(minutes=15)
    api.add_task(content=text, due_datetime=notif_time)
    response = requests.post("https://ntfy.sh/todoist" )
    response.raise_for_status()


if __name__ == "__main__":
    plays_today, info = does_barca_plays_today()
    if plays_today:
        notif_text = f"Barca vs {info.opponent} ({info.competition})"
        set_todoist(notif_text, info)
        send_notification(notif_text)
