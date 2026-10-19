#!/usr/bin/env python3
"""Mirror recent EU court judgments and orders from official CELLAR SPARQL."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
OUT = Path("data/eu-rechtsprechung.json")
now = datetime.now(timezone.utc)
start = (now.date() - timedelta(days=14)).isoformat()
end = now.date().isoformat()
QUERY = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT ?work ?celex ?date ?type WHERE {
  ?work cdm:work_has_resource-type ?type .
  VALUES ?type { <http://publications.europa.eu/resource/authority/resource-type/JUDG>
                 <http://publications.europa.eu/resource/authority/resource-type/ORDER> }
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_date_document ?date .
  FILTER(?date >= "%START%"^^xsd:date && ?date <= "%END%"^^xsd:date)
} ORDER BY DESC(?date) LIMIT 1000""".replace("%START%", start).replace("%END%", end)

def main():
    payload = urlencode({"query": QUERY, "format": "application/sparql-results+json"}).encode()
    request = Request(ENDPOINT, data=payload, headers={
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "feeds-chatgpt/1.0"})
    with urlopen(request, timeout=90) as response:
        data = response.read(8_000_001)
        if response.status != 200 or len(data) > 8_000_000:
            raise ValueError("Bad SPARQL response")
    obj = json.loads(data)
    rows = obj["results"]["bindings"]
    if len(rows) >= 1000:
        raise ValueError("Result limit reached: completeness not assured")
    seen = {}
    for row in rows:
        def value(key):
            return row[key]["value"]
        celex, day, kind = value("celex"), value("date")[:10], value("type").rsplit("/", 1)[-1]
        if not (celex.startswith("6") and len(celex) >= 10 and kind in ("JUDG", "ORDER")
                and start <= day <= end):
            continue
        item = {"celex": celex, "published": day, "type": kind,
                "link": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:" + celex,
                "cellar_work": value("work")}
        previous = seen.get(celex)
        if previous is not None:
            if previous["published"] != day or previous["type"] != kind:
                raise ValueError("Conflicting metadata for CELEX " + celex)
            continue
        seen[celex] = item
    if not seen:
        raise ValueError("No court decisions returned; refusing empty overwrite")
    result = {"feed": "eu-rechtsprechung", "source": ENDPOINT,
              "fetched_at": now.isoformat(timespec="seconds"), "window_start": start,
              "window_end": end, "count": len(seen),
              "items": sorted(seen.values(), key=lambda x: (x["published"], x["celex"]), reverse=True),
              "note": "Official CELLAR metadata. No topical relevance filter; inspect original decisions."}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK CELLAR", len(rows), "raw rows,", len(seen), "unique CELEX")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR CELLAR:", type(exc).__name__, str(exc), file=sys.stderr)
        sys.exit(1)
