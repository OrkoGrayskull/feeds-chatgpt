#!/usr/bin/env python3
"""Optional, bounded vulnerability signals: NVD, GitHub advisories, FIRST EPSS."""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path

import update_feeds as common

NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=3)
CVE = re.compile(r"^CVE-\d{4}-\d{4,}$")
HEADERS = {"User-Agent": "feeds-chatgpt/1.0", "Accept": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data"

def fetch(url):
    with urlopen(Request(url, headers=HEADERS), timeout=25) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("Insecure redirect")
        raw = response.read(6_000_001)
    if not raw or len(raw) > 6_000_000:
        raise ValueError("Empty or oversized API response")
    return json.loads(raw)

def stamp(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except ValueError:
        return None

def github():
    url = "https://api.github.com/advisories?" + urlencode({"type": "reviewed", "per_page": 100, "sort": "published", "direction": "desc"})
    data = fetch(url)
    if not isinstance(data, list):
        raise ValueError("Invalid GitHub advisories response")
    items = []
    for x in data:
        published = stamp(x.get("published_at"))
        if not published or published < START:
            continue
        items.append({"cve": x.get("cve_id"), "ghsa": x.get("ghsa_id"), "title": x.get("summary"),
                      "description": (x.get("description") or "")[:900], "severity": x.get("severity"),
                      "published": published.isoformat(), "link": x.get("html_url")})
    return url, items

def nvd():
    # One bounded query, without an API key or pagination.
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?" + urlencode({
        "pubStartDate": START.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate": NOW.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "resultsPerPage": 200})
    data = fetch(url)
    records = data.get("vulnerabilities")
    if not isinstance(records, list):
        raise ValueError("Invalid NVD response")
    items = []
    for x in records:
        c = x.get("cve", {})
        id_ = c.get("id", "")
        if not CVE.fullmatch(id_):
            continue
        descriptions = c.get("descriptions") or []
        desc = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")
        metrics = c.get("metrics") or {}
        scores = [m.get("cvssData", {}).get("baseScore") for k in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30")
                  for m in metrics.get(k, []) if isinstance(m.get("cvssData", {}).get("baseScore"), (int, float))]
        items.append({"cve": id_, "title": id_, "description": desc[:900],
                      "published": c.get("published"), "last_modified": c.get("lastModified"),
                      "cvss": max(scores) if scores else None,
                      "link": "https://nvd.nist.gov/vuln/detail/" + id_})
    return url, items, data.get("totalResults", 0)

def epss(cves):
    if not cves:
        return None, []
    url = "https://api.first.org/data/v1/epss?" + urlencode({"cve": ",".join(cves[:50])})
    data = fetch(url)
    rows = data.get("data")
    if not isinstance(rows, list):
        raise ValueError("Invalid EPSS response")
    return url, [{"cve": x.get("cve"), "epss": x.get("epss"), "percentile": x.get("percentile"),
                  "date": x.get("date")} for x in rows if CVE.fullmatch(x.get("cve", ""))]

def save(name, source, items, **extra):
    common.write_json(OUT / (name + ".json"), {
        "feed": name, "source": source, "fetched_at": NOW.isoformat(timespec="seconds"),
        "window_hours": 72, "count": len(items), "items": items, **extra})
    print("OK", name, len(items))

def main():
    errors = []
    candidates = []
    try:
        url, items = github()
        if not items:
            raise ValueError("No recent reviewed advisories")
        save("github-advisories", url, items)
        candidates += [x["cve"] for x in items if x.get("cve") and CVE.fullmatch(x["cve"])]
    except Exception as exc:
        errors.append("github-advisories: " + str(exc))
    try:
        url, items, total = nvd()
        if not items:
            raise ValueError("No recent CVEs")
        save("nvd", url, items, total_results=total, truncated=total > len(items))
        candidates += [x["cve"] for x in items if x.get("cvss") is not None and x["cvss"] >= 8.0]
    except Exception as exc:
        errors.append("nvd: " + str(exc))
    # EPSS is an enrichment, not a discovery feed. Include fresh KEV entries if available.
    try:
        kev = json.loads((OUT / "cisa-kev.json").read_text(encoding="utf-8"))
        if kev.get("feed") == "cisa-kev":
            candidates = [x.get("cveID") for x in kev.get("items", [])[:30] if CVE.fullmatch(x.get("cveID", ""))] + candidates
    except (OSError, ValueError, TypeError):
        pass
    # Unique bounded CVEs, one call.
    try:
        cves = list(dict.fromkeys(candidates))[:50]
        if cves:
            url, items = epss(cves)
            if not items:
                raise ValueError("No EPSS results")
            save("epss", url, items, evaluated_cves=len(cves),
                 note="EPSS is a probability estimate, not evidence of exploitation.")
        else:
            print("SKIP epss: no CVE candidates")
    except Exception as exc:
        errors.append("epss: " + str(exc))
    for error in errors:
        print("WARN", error, file=sys.stderr)
    # The workflow step is continue-on-error: signal failed API calls in logs
    # without stopping established feeds or their snapshots.
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
