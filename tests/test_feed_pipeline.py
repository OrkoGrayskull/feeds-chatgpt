"""Offline regression tests for public-source parsers and CVE selection."""
import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import update_feeds as feeds
import update_extra as extra
import update_cellar as cellar
import update_vulnerabilities as vulns

UTC = timezone.utc


def item(day, suffix):
    return {"title": "Notice " + suffix, "link": "https://example.org/" + suffix,
            "published": day, "description": "Source summary"}


def cves(start, count):
    return [f"CVE-2026-{start + n}" for n in range(count)]


class CalendarWindowTests(unittest.TestCase):
    def test_berlin_midnight_and_dst_boundaries(self):
        cases = [
            (datetime(2026, 10, 21, 22, 30, tzinfo=UTC), date(2026, 10, 20), date(2026, 10, 22)),
            (datetime(2026, 3, 29, 1, 30, tzinfo=UTC), date(2026, 3, 27), date(2026, 3, 29)),
            (datetime(2026, 10, 25, 1, 30, tzinfo=UTC), date(2026, 10, 23), date(2026, 10, 25)),
        ]
        for instant, start, end in cases:
            with self.subTest(instant=instant):
                self.assertEqual(feeds.berlin_window(instant), (start, end))

    def test_recent_items_dates_and_offsets(self):
        now = datetime(2026, 10, 21, 10, tzinfo=UTC)
        rows = [
            item("2026-10-18T21:59:00Z", "old"),
            item("2026-10-18T22:30:00Z", "berlin-19"),
            item("2026-10-19", "day-only"),
            item("2026-10-21T08:00:00Z", "today"),
            item("2026-10-22", "future-day"),
        ]
        self.assertEqual([x["link"].rsplit("/", 1)[-1] for x in feeds.recent_items(rows, now)],
                         ["berlin-19", "day-only", "today"])
        self.assertEqual(feeds.recent_items([rows[0]], now), [])
        self.assertEqual(feeds.recent_items([], now), [])

    def test_broken_dates_not_mistaken_for_no_news(self):
        now = datetime(2026, 10, 21, 10, tzinfo=UTC)
        with self.assertRaisesRegex(ValueError, "publication dates"):
            feeds.recent_items([item("not-a-date", "a")], now)


class FeedParsingTests(unittest.TestCase):
    def test_rss_cleaning_and_rfc_timestamp(self):
        rss = b"""<rss version="2.0"><channel><item>
          <title>Current warning</title><link>https://example.org/warning</link>
          <pubDate>Wed, 21 Oct 2026 09:00:00 GMT</pubDate>
          <description>Important &lt;b&gt;update&lt;/b&gt;</description>
        </item></channel></rss>"""
        rows = feeds.parse_feed(rss)
        self.assertEqual(rows[0]["published"], "2026-10-21T09:00:00+00:00")
        self.assertEqual(rows[0]["description"], "Important update")

    def test_atom_and_rdf_formats(self):
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry><title>Atom notice</title><link rel="alternate" href="https://example.org/atom"/>
          <updated>2026-10-21T09:00:00Z</updated><summary>Summary</summary></entry></feed>"""
        rdf = b"""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
          xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
          <item><title>RDF notice</title><link>https://example.org/rdf</link>
          <dc:date>2026-10-21T08:00:00Z</dc:date>
          <description>Summary</description></item></rdf:RDF>"""
        self.assertEqual(feeds.parse_feed(atom)[0]["link"], "https://example.org/atom")
        self.assertEqual(feeds.parse_feed(rdf)[0]["link"], "https://example.org/rdf")

    def test_bad_or_invalid_feed_rejected(self):
        with self.assertRaises(ValueError):
            feeds.parse_feed(b"<rss><channel></channel></rss>")
        with self.assertRaises(Exception):
            feeds.parse_feed(b"<bad>")


class ArchiveAndCacheTests(unittest.TestCase):
    def test_bsi_72h_rolling_archive_and_configured_truncation_threshold(self):
        now = datetime(2026, 10, 21, 10, tzinfo=UTC)
        recent = (now - timedelta(hours=2)).isoformat()
        older = (now - timedelta(hours=74)).isoformat()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "security.json"
            path.write_text(json.dumps({"feed": "security",
                                        "items": [item(recent, "same"), item(older, "outdated")]}),
                            encoding="utf-8")
            incoming = [item(recent, "same"), item(recent, "new")]
            with patch.object(feeds, "OUT", Path(temp)):
                merged, flags = feeds.merge_security_history(incoming, now, source_limit=1000)
                self.assertEqual(len(merged), 2)
                self.assertFalse(flags["source_may_be_truncated"])
                self.assertEqual(flags["history_hours"], 72)
                self.assertTrue(all(x["published"] != older for x in merged))
                _, capped = feeds.merge_security_history(incoming, now, source_limit=2)
                self.assertTrue(capped["source_may_be_truncated"])

    def test_failed_optional_cache_trim_preserves_old_fetched_at(self):
        now = datetime(2026, 10, 21, 10, tzinfo=UTC)
        recorded = "2026-10-20T06:00:00+00:00"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "noyb.json"
            path.write_text(json.dumps({"feed": "noyb", "fetched_at": recorded,
                                        "count": 2, "items": [
                                            item("2026-09-01T00:00:00Z", "old"),
                                            item("2026-10-20T08:00:00Z", "recent")]}),
                            encoding="utf-8")
            with patch.object(feeds, "OUT", Path(temp)):
                feeds.trim_failed_optional_snapshot("noyb", now)
            cache = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(cache["fetched_at"], recorded)
            self.assertEqual(cache["count"], 1)
            self.assertEqual(cache["window_start"], "2026-10-19")


class SpecializedSourceTests(unittest.TestCase):
    def test_kev_catalog_validation_and_three_date_window(self):
        catalog = {"catalogVersion": "1.0", "dateReleased": "2026-10-21",
                   "count": 2, "vulnerabilities": [
                       {"cveID": "CVE-2026-10001", "dateAdded": "2026-10-20"},
                       {"cveID": "CVE-2026-10002", "dateAdded": "2026-10-11"}]}
        window = (date(2026, 10, 19), date(2026, 10, 21))
        with patch.object(extra.common, "berlin_window", return_value=window):
            snapshot = extra.parse_kev(json.dumps(catalog), "https://example.org/catalog")
        self.assertEqual(snapshot["count"], 1)
        self.assertEqual(snapshot["catalog_count"], 2)
        self.assertEqual(snapshot["window_days"], 3)
        bad = {**catalog, "count": 3}
        with self.assertRaises(ValueError):
            extra.parse_kev(json.dumps(bad), "https://example.org/catalog")

    def test_cellar_valid_empty_window(self):
        payload = json.dumps({"results": {"bindings": []}}).encode()
        response = MagicMock()
        response.status = 200
        response.read.return_value = payload
        ctx = MagicMock()
        ctx.__enter__.return_value = response
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "eu-rechtsprechung.json"
            with patch.object(cellar, "OUT", out), patch.object(cellar, "urlopen", return_value=ctx):
                cellar.main()
            obj = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(obj["count"], 0)
        self.assertEqual(obj["items"], [])

    def test_cellar_rejects_truncated_result(self):
        payload = json.dumps({"results": {"bindings": [{}] * 1000}}).encode()
        response = MagicMock()
        response.status = 200
        response.read.return_value = payload
        ctx = MagicMock()
        ctx.__enter__.return_value = response
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(cellar, "OUT", Path(temp) / "eu-rechtsprechung.json"):
                with patch.object(cellar, "urlopen", return_value=ctx):
                    with self.assertRaisesRegex(ValueError, "Result limit"):
                        cellar.main()


class VulnerabilitySelectionTests(unittest.TestCase):
    def test_epss_balances_all_sources_under_saturation(self):
        kev, github, nvd = cves(10000, 35), cves(20000, 75), cves(30000, 56)
        selected = vulns.select_epss_cves(kev, github, nvd)
        self.assertEqual(len(selected), 50)
        self.assertEqual(len(selected), len(set(selected)))
        self.assertEqual(sum(x in kev for x in selected), 20)
        self.assertEqual(sum(x in github for x in selected), 15)
        self.assertEqual(sum(x in nvd for x in selected), 15)

    def test_epss_backfills_unused_slots(self):
        kev, github, nvd = cves(10000, 2), cves(20000, 3), cves(30000, 55)
        selected = vulns.select_epss_cves(kev, github, nvd)
        self.assertEqual(len(selected), 50)
        self.assertTrue(all(x in selected for x in kev + github))
        self.assertEqual(sum(x in nvd for x in selected), 45)

    def test_epss_deduplicates_and_handles_missing_sources(self):
        shared = "CVE-2026-10001"
        selected = vulns.select_epss_cves([shared], [shared, "CVE-2026-20001"], [shared, "invalid"])
        self.assertEqual(selected, [shared, "CVE-2026-20001"])
        self.assertEqual(vulns.select_epss_cves([], [], []), [])

    def test_nvd_reads_latest_page_not_first(self):
        def mocked_fetch(url, timeout=25):
            args = parse_qs(urlparse(url).query)
            if args.get("resultsPerPage") == ["1"]:
                return {"totalResults": 1000}
            self.assertEqual(args.get("startIndex"), ["800"])
            self.assertEqual(args.get("resultsPerPage"), ["200"])
            return {"vulnerabilities": [
                {"cve": {"id": f"CVE-2026-{40000 + n}",
                         "published": f"2026-10-21T09:{n % 60:02d}:00.000",
                         "descriptions": [{"lang": "en", "value": "Test"}],
                         "metrics": {"cvssMetricV31": [
                             {"cvssData": {"baseScore": 9.1}}]}}}
                for n in range(200)]}
        with patch.object(vulns, "fetch", side_effect=mocked_fetch):
            url, items, total = vulns.nvd()
        self.assertEqual(total, 1000)
        self.assertEqual(len(items), 200)
        self.assertIn("startIndex=800", url)
        self.assertEqual(items[0]["cvss"], 9.1)

    def test_nvd_zero_results_and_broken_page(self):
        with patch.object(vulns, "fetch", return_value={"totalResults": 0}) as fetch:
            _, items, count = vulns.nvd()
        self.assertEqual((items, count), ([], 0))
        fetch.assert_called_once()
        with patch.object(vulns, "fetch", side_effect=[
            {"totalResults": 300}, {"vulnerabilities": []}
        ]):
            with self.assertRaisesRegex(ValueError, "NVD page"):
                vulns.nvd()


if __name__ == "__main__":
    unittest.main()
