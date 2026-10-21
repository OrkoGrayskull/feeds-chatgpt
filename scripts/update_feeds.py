#!/usr/bin/env python3
"""Mirror configured public RSS/Atom feeds into validated JSON snapshots."""
import html
import json
import re
import sys
import tempfile
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, date, timezone, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, urljoin

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "feeds.json"
OUT = ROOT / "data"
MAX_BYTES = 3_000_000
MAX_ITEMS = 100
BERLIN = ZoneInfo("Europe/Berlin")
RECENT_DAYS = 3  # Today and the two previous calendar days in Germany.
ATOM = "{http://www.w3.org/2005/Atom}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RSS1 = "{http://purl.org/rss/1.0/}"
DC = "{http://purl.org/dc/elements/1.1/}"

class StripHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)

def clean(raw):
    parser = StripHTML()
    parser.feed(raw or "")
    parser.close()
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()

def iso_date(raw):
    if not raw:
        return None
    try:
        d = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        try:
            d = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc).isoformat(timespec="seconds")


def berlin_window(now=None, days=RECENT_DAYS):
    """Inclusive calendar dates in Europe/Berlin, not an arbitrary 72h offset."""
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(BERLIN).date()
    return today - timedelta(days=days - 1), today


def recent_items(items, now=None, days=RECENT_DAYS):
    """Only published items from the chosen local calendar dates; undated items excluded."""
    start, end = berlin_window(now, days)
    filtered = []
    for item in items:
        value = item.get("published")
        if not isinstance(value, str):
            continue
        try:
            if len(value) == 10:
                published_day = date.fromisoformat(value)
            else:
                stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                published_day = stamp.astimezone(BERLIN).date()
        except ValueError:
            continue
        if start <= published_day <= end:
            filtered.append(item)
    return filtered

def download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "feeds-chatgpt/1.0",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        if urlparse(response.geturl()).scheme != "https":
            raise ValueError("Redirect to non-HTTPS URL")
        result = response.read(MAX_BYTES + 1)
    if not result or len(result) > MAX_BYTES:
        raise ValueError("Empty or oversized feed")
    return result

def parse_feed(content, max_items=MAX_ITEMS, description_limit=None, legacy_link_base=None):
    root = ET.fromstring(content)
    result = []
    if root.tag == "rss":
        for item in root.findall("./channel/item")[:max_items]:
            result.append({
                "title": clean(item.findtext("title")) or clean(re.split(r"</p>|<br\s*/?>", item.findtext("description") or "", maxsplit=1, flags=re.I)[0])[:180],
                "link": (item.findtext("link") or "").strip(),
                "published": iso_date(item.findtext("pubDate")),
                "description": clean(item.findtext("description"))[:description_limit] if description_limit else clean(item.findtext("description")),
            })
    elif root.tag == RDF + "RDF":
        for item in root.findall(RSS1 + "item")[:max_items]:
            desc = clean(item.findtext(RSS1 + "description"))
            result.append({
                "title": clean(item.findtext(RSS1 + "title")),
                "link": (item.findtext(RSS1 + "link") or "").strip(),
                "published": iso_date(item.findtext(DC + "date")),
                "description": desc[:description_limit] if description_limit else desc,
            })
    elif root.tag == ATOM + "feed":
        for entry in root.findall(ATOM + "entry")[:max_items]:
            links = entry.findall(ATOM + "link")
            selected = next((x for x in links if x.get("rel", "alternate") == "alternate" and x.get("href")), None)
            if selected is None:
                selected = next((x for x in links if x.get("href")), None)
            result.append({
                "title": clean(entry.findtext(ATOM + "title")),
                "link": selected.get("href", "") if selected is not None else "",
                "published": iso_date(entry.findtext(ATOM + "updated") or entry.findtext(ATOM + "published")),
                "description": clean(entry.findtext(ATOM + "summary") or entry.findtext(ATOM + "content"))[:description_limit] if description_limit else clean(entry.findtext(ATOM + "summary") or entry.findtext(ATOM + "content")),
            })
    else:
        raise ValueError("Unsupported feed format (expected RSS 1.0/RDF, RSS 2.0 or Atom)")
    if legacy_link_base:
        # BayLfD may publish HTTP or relative item links.
        # Normalize only links pointing to the official authority domain.
        for item in result:
            link = urljoin(legacy_link_base, item["link"])
            parsed = urlparse(link)
            if parsed.scheme in ("http", "https") and parsed.hostname in ("datenschutz-bayern.de", "www.datenschutz-bayern.de"):
                item["link"] = parsed._replace(scheme="https").geturl()
    result = [item for item in result if item["title"] and urlparse(item["link"]).scheme == "https"]
    if not result:
        raise ValueError("No valid feed entries")
    return result

def write_json(path, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".feed-", suffix=".json", dir=OUT)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def merge_security_history(items, now):
    """Retain 72 hours of BSI observations for the optional 72h fallback."""
    cutoff = now - timedelta(hours=72)
    path = OUT / "security.json"
    fresh_count = len(items)
    oldest_fresh = min((x["published"] for x in items if x.get("published")), default=None)
    if path.exists():
        try:
            previous = json.loads(path.read_text(encoding="utf-8"))
            if previous.get("feed") == "security":
                items = items + [x for x in previous.get("items", [])
                                 if isinstance(x, dict) and x.get("title")
                                 and x.get("link") and x.get("published")]
        except (OSError, ValueError, TypeError):
            pass
    unique = {}
    for item in items:
        published = iso_date(item.get("published"))
        if not published:
            continue
        when = datetime.fromisoformat(published)
        if when < cutoff or when > now + timedelta(minutes=10):
            continue
        key = item["link"].split("#", 1)[0]
        if key not in unique or published > unique[key]["published"]:
            unique[key] = {**item, "published": published}
    retained = sorted(unique.values(), key=lambda x: (x["published"], x["link"]), reverse=True)
    archive_truncated = len(retained) > 1800
    retained = retained[:1800]  # Keep the GitHub-file API readable.
    return retained, {
        "archive_truncated": archive_truncated,
        "history_item_limit": 1800,
        "source_count": fresh_count,
        "source_oldest_published": oldest_fresh,
        "history_cutoff": cutoff.isoformat(timespec="seconds"),
        "history_hours": 72,
        "source_may_be_truncated": bool(
            fresh_count >= 100 and oldest_fresh
            and datetime.fromisoformat(iso_date(oldest_fresh)) >= now - timedelta(hours=72)
        ),
        "note": "Rolling observed BSI items; gaps in the upstream feed cannot be ruled out.",
    }

def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    feeds = config["feeds"]
    if "--security-only" in sys.argv[1:]:
        feeds = [f for f in feeds if f["id"] in ("security", "buergercert")]
    failures = []
    seen = set()
    for feed in feeds:
        if feed.get("type", "rss") != "rss":
            continue  # handled by the supplemental updater
        name, url = feed["id"], feed["url"]
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,49}", name) or name in seen:
            raise ValueError("Invalid or duplicate feed id: " + name)
        seen.add(name)
        if urlparse(url).scheme != "https":
            raise ValueError("Only HTTPS URLs are supported")
        try:
            items = parse_feed(download(url), max_items=feed.get("max_items", MAX_ITEMS), description_limit=feed.get("description_limit"), legacy_link_base=url if name == "baylfd" else None)
            fetched = datetime.now(timezone.utc)
            if name == "security":
                # Security is the sole rolling-72h RSS exception: preserve the
                # existing optional 72h IT-security fallback despite RSS limits.
                items, extra = merge_security_history(items, fetched)
            else:
                original_count = len(items)
                items = recent_items(items, fetched)
                start, end = berlin_window(fetched)
                extra = {"source_count": original_count, "window_days": RECENT_DAYS,
                         "window_start": start.isoformat(), "window_end": end.isoformat()}
            write_json(OUT / (name + ".json"), {
                "feed": name, "source": url,
                "fetched_at": fetched.isoformat(timespec="seconds"),
                "count": len(items), "items": items, **extra,
            })
            print("OK:", name, len(items), "items")
        except Exception as exc:
            if not feed.get("optional", False):
                failures.append(name)
            print("ERROR:", name, str(exc), file=sys.stderr)
    if failures:
        print("Failed feeds:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
