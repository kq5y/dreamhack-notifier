# dreamhack-notifier

Notifies you of new issues and daily progress for dreamhack's wargame

## Usage

```bash
echo '{}' > app/challenges.json
echo '{}' > app/stats.json
```

```bash
docker build -t dreamhack-notifier .
docker run -d \
  --name dreamhack-notifier \
  --restart unless-stopped \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/XXXXXXXX/XXXXXXXX" \
  -e CHECK_INTERVAL="60" \
  -e TARGET_USER_ID="xxxxxxx" \
  -e TIMEZONE="Asia/Tokyo" \
  dreamhack-notifier
```

## License

[MIT License](LICENSE)
