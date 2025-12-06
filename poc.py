import os
import requests
from datetime import datetime, timezone, timedelta

ORG_ID = os.environ["ATLAS_ORG_ID"]
API_KEY = os.environ["ATLAS_API_KEY"]  # Admin API key from admin.atlassian.com
BASE_URL = f"https://api.atlassian.com/admin/v1/orgs/{ORG_ID}/users"

THRESHOLD_DAYS = 40
threshold = datetime.now(timezone.utc) - timedelta(days=THRESHOLD_DAYS)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

inactive_users = []

url = BASE_URL
while url:
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    payload = resp.json()

    for user in payload.get("data", []):
        last_active_str = user.get("last_active")
        if not last_active_str:
            # Treat no last_active as "never active" -> count as inactive
            inactive_users.append({**user, "reason": "no last_active"})
            continue

        last_active = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
        if last_active < threshold:
            inactive_users.append({**user, "reason": f"last_active<{THRESHOLD_DAYS}d"})

    # Handle pagination
    links = payload.get("links", {})
    next_link = links.get("next")
    if next_link:
        # When Atlassian returns a cursor, you usually need to re-hit the same endpoint with ?cursor=...
        url = f"{BASE_URL}?cursor={next_link}"
    else:
        url = None

print(f"Found {len(inactive_users)} inactive users (> {THRESHOLD_DAYS} days):")
for u in inactive_users:
    print(f"- {u.get('email')} ({u.get('name')}), last_active={u.get('last_active')}, reason={u['reason']}")
