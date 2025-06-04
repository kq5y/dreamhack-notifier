import re
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

import config


def parse_entry_date(entry, key) -> datetime:
    raw = entry.get(key)
    if not raw:
        return None
    try:
        dt_utc = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=timezone.utc)
        return dt_utc
    except Exception:
        return None


def format_datetime(dt: datetime, tz_name: str) -> str:
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = timezone.utc
    local_dt = dt.astimezone(tz)
    tz_abbr = local_dt.tzname() or ""
    return local_dt.strftime(f"%Y-%m-%d %H:%M {tz_abbr}")


def load_challenges() -> list:
    try:
        with open(config.CHALLENGES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_challenges(challenges: list):
    with open(config.CHALLENGES_FILE, "w", encoding="utf-8") as f:
        json.dump(challenges, f, ensure_ascii=False)


def load_stats_updated() -> str | None:
    try:
        with open(config.STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("updated", None)
    except FileNotFoundError:
        return None


def save_stats_updated(updated: str):
    with open(config.STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": updated}, f, ensure_ascii=False)


def get_new_challenges() -> list:
    prev_challenges = load_challenges()
    prev_challenges_set = {ch["id"] for ch in prev_challenges}

    response = requests.get(f"{config.API_HOST}/challenges/", params={
        "page": 1,
        #"search": "",
        #"ordering": "",
        #"scope": "",
        #"category": "",
        #"status": "",
        #"difficulty": "",
        #"type": "",
        "page_size": 20,
    })
    if response.status_code != 200:
        raise Exception(f"Failed to fetch challenges: {response.status_code}")

    response_json = response.json()
    challenges = response_json.get("results", [])
    save_challenges(challenges)

    new_challenges = [ch for ch in challenges if ch["id"] not in prev_challenges_set]
    return new_challenges


def get_stats(userid: str) -> list:
    response = requests.get(f"{config.API_HOST}/stats/", params={
        "limit": 100,
        "offset": 0,
        "ordering": "-solved_at",
        #"search": "",
        "user_id": userid,
    })
    if response.status_code != 200:
        raise Exception(f"Failed to fetch stats: {response.status_code}")
    
    response_json = response.json()
    return response_json.get("results", [])


def build_event_embed(entry, title: str, link: str, public_at_local: str | None) -> dict:
    tags = entry.get("tags", [])
    challenge_id = entry.get("id", "Unknown ID")
    author_name = entry.get("author", {}).get("nickname", "Unknown Author")
    author_icon = entry.get("author", {}).get("profile_image", "")
    embed_title = f"🆕 New Challenge: {title}"
    color = 0x12FF34
    embed: dict = {
        "title": embed_title,
        "url": link,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {
                "name": "ID",
                "value": str(challenge_id),
                "inline": True
            },
            {
                "name": "Author",
                "value": author_name,
                "inline": True
            },
            {
                "name": "Tags",
                "value": ", ".join(tags) if tags else "No Tags",
                "inline": True
            }
        ],
    }
    if author_icon:
        embed["thumbnail"] = {"url": author_icon}
    if public_at_local:
        embed["fields"].insert(1, {
            "name": "Published At",
            "value": public_at_local,
            "inline": True
        })
    return embed


def send_discord_embed(embed: dict):
    payload = {"embeds": [embed]}
    try:
        resp = requests.post(config.WEBHOOK_URL, json=payload)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to send Discord embed: {e}")


def main():
    print(f"[INFO] Launch: interval={config.CHECK_INTERVAL}, timezone={config.TIMEZONE}")

    while True:
        # Check New Challenges
        try:
            new_challenges = get_new_challenges()
            if new_challenges:
                print(f"[INFO] Found {len(new_challenges)} new challenges.")
                for challenge in new_challenges:
                    challenge_id = challenge.get("id")
                    title = challenge.get("title", "Unknown Challenge")
                    link = f"https://dreamhack.io/wargame/challenges/{challenge_id}/"
                    public_at_utc = parse_entry_date(challenge, "public_at")
                    if public_at_utc:
                        public_at_local = format_datetime(public_at_utc, config.TIMEZONE)
                    else:
                        public_at_local = None
                    embed = build_event_embed(challenge, title, link, public_at_local)
                    send_discord_embed(embed)
                    print(f"[NOTIFY] New Challenge: {title} - {link}")

        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")
        
        # Check Stats (daily)
        try:
            stats_updated = load_stats_updated()
            now_date_local = datetime.now(timezone.utc).astimezone(ZoneInfo(config.TIMEZONE))
            if not stats_updated or datetime.strptime(stats_updated, "%Y-%m-%d").date() < now_date_local.date():
                print("[INFO] Checking stats...")
                stats = get_stats(config.TARGET_USER_ID)
                if stats:
                    solved_count = 0
                    earned_points = 0
                    for entry in stats:
                        solved_at_utc = parse_entry_date(entry, "solved_at")
                        solved_at_local = solved_at_utc.astimezone(ZoneInfo(config.TIMEZONE)) if solved_at_utc else None
                        if solved_at_local and solved_at_local.date() + 1 == now_date_local.date():
                            solved_count += 1
                            earned_points += entry.get("earned_points", 0)
                    print(f"[INFO] Today's solved count: {solved_count}, Points: {earned_points}")
                    embed = {
                        "title": "Daily Stats Update",
                        "description": f"**{now_date_local.strftime('%Y-%m-%d')}**",
                        "color": 0x34FF12,
                        "fields": [
                            {
                                "name": "Solved Challenges",
                                "value": str(solved_count),
                                "inline": True
                            },
                            {
                                "name": "Earned Points",
                                "value": str(earned_points),
                                "inline": True
                            }
                        ],
                        "timestamp": now_date_local.isoformat(),
                    }
                    send_discord_embed(embed)
                    save_stats_updated(now_date_local.strftime("%Y-%m-%d"))
                    print("[NOTIFY] Daily stats updated.")
                else:
                    print("[INFO] No stats found.")
        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")
        
        time.sleep(config.CHECK_INTERVAL)


if __name__ == "__main__":
    main()
