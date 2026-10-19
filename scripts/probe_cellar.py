#!/usr/bin/env python3
"""Diagnostic only: query official CELLAR SPARQL for EU court judgments/orders."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
QUERY = """PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
SELECT DISTINCT ?work ?celex ?date ?type WHERE {
  ?work cdm:work_has_resource-type ?type .
  VALUES ?type { <http://publications.europa.eu/resource/authority/resource-type/JUDG>
                 <http://publications.europa.eu/resource/authority/resource-type/ORDER> }
  ?work cdm:resource_legal_id_celex ?celex .
  ?work cdm:work_date_document ?date .
  FILTER(?date >= "2026-10-01"^^<http://www.w3.org/2001/XMLSchema#date>)
} ORDER BY DESC(?date) LIMIT 10"""
out = {"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
       "source":ENDPOINT,"production_ready":False,"status":"failed"}
try:
    payload=urlencode({"query":QUERY,"format":"application/sparql-results+json"}).encode()
    req=Request(ENDPOINT,data=payload,headers={"Accept":"application/sparql-results+json",
         "Content-Type":"application/x-www-form-urlencoded","User-Agent":"feeds-chatgpt/1.0"})
    with urlopen(req,timeout=50) as res:
        raw=res.read(1000000)
        out["http_status"]=res.status
        out["content_type"]=res.headers.get("Content-Type","")
    obj=json.loads(raw)
    rows=obj.get("results",{}).get("bindings",[])
    out["count"]=len(rows)
    out["sample"]=[{k:v.get("value") for k,v in row.items()} for row in rows[:10]]
    out["status"]="query_success" if rows else "query_empty"
    out["note"]="Diagnostic only; date coverage, metadata and completeness not yet validated"
except Exception as exc:
    out["error"]=type(exc).__name__+": "+str(exc)
Path("data").mkdir(exist_ok=True)
Path("data/cellar-probe.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(out,ensure_ascii=False))
