#!/usr/bin/env python3
"""Optional Bluesky search signals. Failure never blocks other feeds."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
QUERIES = ["CVE", "actively exploited", "security advisory", "Datenschutz", "DSGVO", "GDPR", "data breach", "privacy", "Überwachung", "surveillance"]
ACCOUNTS = [
    "noyb.eu", "datenschutz.bsky.social", "bleepingcomputer.com",
    "ammir.bsky.social", "responsible.fyi", "eff.org",
    "netzpolitik.org", "ccc.de", "infosec.skyfleet.blue",
    "insecurestack.bsky.social",
]
AUTHOR_FEED = "https://api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
OUT = Path(__file__).resolve().parent.parent / "data" / "bluesky.json"

def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    items = {}
    errors = []
    def add_post(post, source, label):
        uri = post.get("uri", "")
        record = post.get("record") or {}
        created = record.get("createdAt", "")
        if not uri.startswith("at://") or not created or record.get("reply"):
            return False
        try:
            published = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            return False
        if not cutoff <= published <= now + timedelta(minutes=5):
            return False
        author = post.get("author") or {}
        handle = author.get("handle", "")
        rkey = uri.rsplit("/", 1)[-1]
        if not handle or not rkey:
            return False
        if uri not in items:
            items[uri] = {"title": (record.get("text") or "")[:180], "description": (record.get("text") or "")[:1200], "link": "https://bsky.app/profile/" + handle + "/post/" + rkey, "published": created, "author": handle, "uri": uri, "queries": [], "accounts": []}
        if label not in items[uri][source]:
            items[uri][source].append(label)
        return True

    for term in QUERIES:
        url = BASE + "?" + urlencode({"q": term, "limit": 50, "sort": "latest", "since": cutoff.isoformat(timespec="seconds").replace("+00:00", "Z")})
        try:
            req = Request(url, headers={"User-Agent": "feeds-chatgpt/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=15) as response:
                payload = json.load(response)
            if not isinstance(payload.get("posts"), list):
                raise ValueError("Missing posts array")
            for post in payload["posts"]:
                add_post(post, "queries", term)
            print("OK", term, "received", len(payload["posts"]))
        except Exception as exc:
            errors.append({"query": term, "error": type(exc).__name__})
            print("ERROR", term, type(exc).__name__)
    for account in ACCOUNTS:
        url = AUTHOR_FEED + "?" + urlencode({"actor": account, "limit": 20, "filter": "posts_no_replies"})
        try:
            req = Request(url, headers={"User-Agent": "feeds-chatgpt/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=15) as response:
                payload = json.load(response)
            if not isinstance(payload.get("feed"), list):
                raise ValueError("Missing feed array")
            accepted = 0
            for entry in payload["feed"]:
                if entry.get("reason") or not isinstance(entry.get("post"), dict):
                    continue  # exclude reposts
                post = entry["post"]
                if (post.get("author") or {}).get("handle", "").lower() != account.lower():
                    continue
                accepted += int(add_post(post, "accounts", account))
            print("OK account", account, "accepted", accepted)
        except Exception as exc:
            errors.append({"account": account, "error": type(exc).__name__})
            print("ERROR account", account, type(exc).__name__)
    if not items:
        print("No usable Bluesky results: keeping prior snapshot")
        return 0
    result = {"feed": "bluesky", "source": BASE, "fetched_at": now.isoformat(timespec="seconds"), "window_hours": 24, "queries": QUERIES, "monitored_accounts": ACCOUNTS, "errors": errors, "count": len(items), "items": sorted(items.values(), key=lambda x: x["published"], reverse=True)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
