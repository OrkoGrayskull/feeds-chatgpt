#!/usr/bin/env python3
"""One-off InfoCuria accessibility and parseability probe, not a production feed."""
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.request import Request, urlopen

URL = "https://infocuria.curia.europa.eu/tabs/jurisprudence?doc-date-start=2026-10-12&lang=en&sort=doc_date-desc"
OUTPUT = "data/infocuria-probe.json"

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.hidden:
            self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())

def main():
    result = {"source": URL, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "status": "failed", "production_ready": False}
    try:
        request = Request(URL, headers={"User-Agent": "Mozilla/5.0 (compatible; public-source-research/1.0)",
                                        "Accept": "text/html"})
        with urlopen(request, timeout=25) as response:
            data = response.read(3_000_001)
            result["http_status"] = response.status
            result["content_type"] = response.headers.get("Content-Type", "")
            result["bytes"] = len(data)
            if len(data) > 3_000_000:
                raise ValueError("Response exceeds 3 MB probe limit")
        html = data.decode("utf-8", errors="replace")
        parser = VisibleText()
        parser.feed(html)
        content = " ".join(parser.parts)
        result["contains_ecli"] = bool(re.search(r"ECLI:EU:[CTF]:\\d{4}:\\d+", content))
        result["contains_document_types"] = bool(re.search(r"Urteil|Beschluss|Judgment|Order", content, re.I))
        result["sample_eclis"] = list(dict.fromkeys(re.findall(r"ECLI:EU:[CTF]:\\d{4}:\\d+", content)))[:8]
        result["status"] = "readable" if result["contains_ecli"] and result["contains_document_types"] else "unstructured_or_empty"
        result["note"] = ("Readability only. Date filtering, text search, pagination, original-document links "
                          "and completeness are NOT validated. Do not consume as a daily legal feed.")
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    from pathlib import Path
    Path("data").mkdir(exist_ok=True)
    Path(OUTPUT).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "readable" else 1

if __name__ == "__main__":
    sys.exit(main())
