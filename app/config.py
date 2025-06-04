import os

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is not set.")

TARGET_USER_ID = os.getenv("TARGET_USER_ID")
if not TARGET_USER_ID:
    raise ValueError("TARGET_USER_ID environment variable is not set.")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 120))
if CHECK_INTERVAL <= 0:
    raise ValueError("CHECK_INTERVAL must be a positive integer.")

TIMEZONE = os.getenv("TIMEZONE", "Asia/Tokyo")
if not TIMEZONE:
    raise ValueError("TIMEZONE environment variable is not set.")

API_HOST = "https://dreamhack.io/api/v1/wargame"

CHALLENGES_FILE = "challenges.json"
STATS_FILE = "stats.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0"
