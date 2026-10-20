#!/usr/bin/env python3
"""Optional Bluesky search signals. Failure never blocks other feeds."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts"
QUERIES = ["CVE", "actively exploited", "security advisory", "Datenschutz", "DSGVO", "GDPR", "data breach", "privacy", "Überwachung", "surveillance"]
OUT = Path(__file__).resolve().parent.parent / "data" / "bluesky.json"

def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    items = {}
    errors = []
    for term in QUERIES:
        url = BASE + "?" + urlencode({"q": term, "limit": 50, "sort": "latest", "since": cutoff.isoformat(timespec="seconds").replace("+00:00", "Z")})
        try:
            req = Request(url, headers={"User-Agent": "feeds-chatgpt/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=15) as response:
                payload = json.load(response)
            if not isinstance(payload.get("posts"), list):
                raise ValueError("Missing posts array")
            for post in payload["posts"]:
                uri = post.get("uri", "")
                record = post.get("record") or {}
                created = record.get("createdAt", "")
                if not uri.startswith("at://") or not created:
                    continue
                try:
                    published = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if published < cutoff or published > now + timedelta(minutes=5):
                    continue
                author = post.get("author") or {}
                handle = author.get("handle", "")
                rkey = uri.rsplit("/", 1)[-1]
                if not handle or not rkey:
                    continue
                link = "https://bsky.app/profile/" + handle + "/post/" + rkey
                if uri not in items:
                    items[uri] = {"title": (record.get("text") or "")[:180], "description": (record.get("text") or "")[:1200], "link": link, "published": created, "author": handle, "uri": uri, "queries": []}
                items[uri]["queries"].append(term)
            print("OK", term, "received", len(payload["posts"]))
        except Exception as exc:
            errors.append({"query": term, "error": type(exc).__name__})
            print("ERROR", term, type(exc).__name__)
    if not items:
        print("No usable Bluesky results: keeping prior snapshot")
        return 0
    result = {"feed": "bluesky", "source": BASE, "fetched_at": now.isoformat(timespec="seconds"), "window_hours": 24, "queries": QUERIES, "errors": errors, "count": len(items), "items": sorted(items.values(), key=lambda x: x["published"], reverse=True)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
