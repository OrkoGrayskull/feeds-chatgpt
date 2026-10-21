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
TODAY_BERLIN = NOW.astimezone(common.BERLIN).date()
START_DAY = TODAY_BERLIN - timedelta(days=2)
START = datetime.combine(START_DAY, datetime.min.time(), tzinfo=common.BERLIN).astimezone(timezone.utc)
CVE = re.compile(r"^CVE-\d{4}-\d{4,}$")
HEADERS = {"User-Agent": "feeds-chatgpt/1.0", "Accept": "application/json"}
OUT = Path(__file__).resolve().parents[1] / "data"
EPSS_LIMIT = 50

def fetch(url, timeout=25):
    with urlopen(Request(url, headers=HEADERS), timeout=timeout) as response:
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
        if not published or published < START or published > NOW + timedelta(minutes=5):
            continue
        items.append({"cve": x.get("cve_id"), "ghsa": x.get("ghsa_id"), "title": x.get("summary"),
                      "description": (x.get("description") or "")[:900], "severity": x.get("severity"),
                      "published": published.isoformat(), "link": x.get("html_url")})
    return url, items

def nvd():
    """Read a bounded, latest-first selection from the NVD's oldest-first pages."""
    endpoint = "https://services.nvd.nist.gov/rest/json/cves/2.0?"
    params = {
        "pubStartDate": START.strftime("%Y-%m-%dT%H:%M:%S.000"),
        "pubEndDate": NOW.strftime("%Y-%m-%dT%H:%M:%S.000"),
    }
    # Discover the result count before selecting the latest 200. The first
    # page alone would miss the newest entries in busy publication periods.
    head_url = endpoint + urlencode({**params, "resultsPerPage": 1})
    summary = fetch(head_url, timeout=45)
    total = summary.get("totalResults")
    if not isinstance(total, int) or total < 0:
        raise ValueError("Invalid NVD totalResults")
    if total == 0:
        return head_url, [], 0
    page_size = min(200, total)
    index = max(0, total - page_size)
    url = endpoint + urlencode({**params, "resultsPerPage": page_size,
                                "startIndex": index})
    data = fetch(url, timeout=45)
    records = data.get("vulnerabilities")
    if not isinstance(records, list) or not records:
        raise ValueError("Invalid or empty latest NVD page")
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
    items.sort(key=lambda x: (x["published"] or "", x["cve"]), reverse=True)
    return url, items, total

def select_epss_cves(kev_cves, github_cves, nvd_cves):
    """Prioritize exploited CVEs while reserving EPSS coverage for each source.

    Each source receives a guaranteed allocation when it has enough distinct
    candidates. Unused places are reassigned, without duplicate CVEs or calls.
    """
    groups = ((kev_cves, 20), (github_cves, 15), (nvd_cves, 15))
    result, seen = [], set()

    def append(values, cap):
        added = 0
        for cve in values:
            if not isinstance(cve, str) or not CVE.fullmatch(cve) or cve in seen:
                continue
            result.append(cve)
            seen.add(cve)
            added += 1
            if len(result) == EPSS_LIMIT or added >= cap:
                break

    for values, reserved in groups:
        if len(result) == EPSS_LIMIT:
            break
        append(values, reserved)
    # Backfill without overriding the other sources' reserved slots.
    for values in (kev_cves, nvd_cves, github_cves):
        if len(result) == EPSS_LIMIT:
            break
        append(values, EPSS_LIMIT - len(result))
    return result


def epss(cves):
    if not cves:
        return None, []
    url = "https://api.first.org/data/v1/epss?" + urlencode({"cve": ",".join(cves[:EPSS_LIMIT])})
    data = fetch(url)
    rows = data.get("data")
    if not isinstance(rows, list):
        raise ValueError("Invalid EPSS response")
    return url, [{"cve": x.get("cve"), "epss": x.get("epss"), "percentile": x.get("percentile"),
                  "date": x.get("date")} for x in rows if CVE.fullmatch(x.get("cve", ""))]

def save(name, source, items, **extra):
    common.write_json(OUT / (name + ".json"), {
        "feed": name, "source": source, "fetched_at": NOW.isoformat(timespec="seconds"),
        "window_days": 3, "window_start": START_DAY.isoformat(),
        "window_end": TODAY_BERLIN.isoformat(),
        "count": len(items), "items": items, **extra})
    print("OK", name, len(items))

def main():
    errors = []
    github_cves, nvd_cves, kev_cves = [], [], []
    try:
        url, items = github()
        save("github-advisories", url, items)
        github_cves = [x["cve"] for x in items if x.get("cve") and CVE.fullmatch(x["cve"])]
    except Exception as exc:
        errors.append("github-advisories: " + str(exc))
    try:
        url, items, total = nvd()
        save("nvd", url, items, total_results=total, truncated=total > len(items),
             selection="latest_published", start_index=max(0, total - 200))
        # High severity first, then publication recency. NVD must not be
        # crowded out just because GitHub returned many reviewed advisories.
        nvd_cves = [x["cve"] for x in sorted(
            items, key=lambda x: (x.get("cvss") or 0, x.get("published") or ""), reverse=True
        ) if x.get("cvss") is not None and x["cvss"] >= 8.0]
    except Exception as exc:
        errors.append("nvd: " + str(exc))
    # EPSS is an enrichment, not a discovery feed. Include fresh KEV entries if available.
    try:
        kev = json.loads((OUT / "cisa-kev.json").read_text(encoding="utf-8"))
        if kev.get("feed") == "cisa-kev":
            kev_cves = [x.get("cveID") for x in kev.get("items", [])[:30]
                        if CVE.fullmatch(x.get("cveID", ""))]
    except (OSError, ValueError, TypeError):
        pass
    # Balanced, deduplicated candidate set; a single bounded EPSS request.
    try:
        cves = select_epss_cves(kev_cves, github_cves, nvd_cves)
        if cves:
            url, items = epss(cves)
            if not items:
                raise ValueError("No EPSS results")
            save("epss", url, items, evaluated_cves=len(cves),
                 note="EPSS is a probability estimate, not evidence of exploitation.")
        else:
            save("epss", "https://api.first.org/data/v1/epss", [],
                 evaluated_cves=0, note="No eligible recent CVEs; no EPSS query required.")
    except Exception as exc:
        errors.append("epss: " + str(exc))
    for error in errors:
        print("WARN", error, file=sys.stderr)
    # The workflow step is continue-on-error: signal failed API calls in logs
    # without stopping established feeds or their snapshots.
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
