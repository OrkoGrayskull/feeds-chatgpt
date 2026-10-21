#!/usr/bin/env python3
"""Publish supplemental public sources as compact dated JSON snapshots."""
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.error import HTTPError, URLError

import update_feeds as common

common.MAX_BYTES = 6_000_000


def parse_kev(payload, url):
    catalog = json.loads(payload)
    records = catalog.get('vulnerabilities')
    if not isinstance(records, list) or not records or catalog.get('count') != len(records):
        raise ValueError('Invalid KEV catalog or mismatched count')
    if not catalog.get('catalogVersion') or not common.iso_date(catalog.get('dateReleased')):
        raise ValueError('Missing KEV catalog version or release date')
    cutoff, today = common.berlin_window()
    recent = []
    for record in records:
        cve = record.get('cveID', '')
        added = record.get('dateAdded', '')
        if not re.fullmatch(r'CVE-\d{4}-\d{4,}', cve):
            raise ValueError('Malformed KEV CVE identifier')
        try:
            added_date = date.fromisoformat(added)
        except (ValueError, TypeError) as exc:
            raise ValueError('Malformed KEV dateAdded') from exc
        if cutoff <= added_date <= today:
            recent.append({key: record.get(key) for key in (
                'cveID', 'dateAdded', 'vendorProject', 'product', 'vulnerabilityName',
                'shortDescription', 'requiredAction', 'dueDate', 'knownRansomwareCampaignUse', 'notes'
            )})
    recent.sort(key=lambda x: (x['dateAdded'], x['cveID']), reverse=True)
    return {
        'feed': 'cisa-kev', 'source': url,
        'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'catalogVersion': catalog['catalogVersion'],
        'dateReleased': catalog['dateReleased'],
        'catalog_count': len(records),
        'window_days': 3, 'window_start': cutoff.isoformat(),
        'window_end': today.isoformat(),
        'count': len(recent), 'items': recent,
    }


class JSONLD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.current = []
        self.blobs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.in_script = True
            self.current = []

    def handle_data(self, data):
        if self.in_script:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.in_script:
            self.blobs.append(''.join(self.current))
            self.in_script = False


class PressList(HTMLParser):
    """Pair dated press-list items with their official article links."""
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.position = 0
        self.last_date = None
        self.active = None
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a' or self.active is not None:
            return
        href = dict(attrs).get('href', '')
        link = urljoin(self.base, href)
        host = urlparse(link).hostname
        if host not in ('bfdi.bund.de', 'www.bfdi.bund.de'):
            return
        if '/SharedDocs/Pressemitteilungen/DE/' not in link or '.html' not in link:
            return
        if self.last_date is None or self.position - self.last_date[1] > 800:
            return
        self.active = {'published': self.last_date[0], 'link': link, 'parts': []}

    def handle_data(self, data):
        if self.active is not None:
            self.active['parts'].append(data)
        for match in re.finditer(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', data):
            try:
                published = datetime.strptime(match.group(), '%d.%m.%Y').date().isoformat()
                self.last_date = (published, self.position + match.end())
            except ValueError:
                pass
        self.position += len(data)

    def handle_endtag(self, tag):
        if tag != 'a' or self.active is None:
            return
        title = common.clean(''.join(self.active['parts']))
        if title and len(title) >= 8:
            self.items.append({
                'title': title, 'link': self.active['link'],
                'published': self.active['published'], 'description': ''
            })
        self.active = None


def parse_bfdi_html(payload, source):
    parser = PressList(source)
    parser.feed(payload.decode('utf-8', errors='replace'))
    seen = set()
    items = []
    for item in parser.items:
        if item['link'] not in seen:
            seen.add(item['link'])
            items.append(item)
    if len(items) < 5:
        raise ValueError('Fewer than five reliably dated official press links in listing')
    items.sort(key=lambda x: x['published'], reverse=True)
    return items[:100]

def download_bfdi(url):
    """One bounded retry for transient failures of this central upstream source."""
    try:
        return common.download(url)
    except (TimeoutError, URLError) as exc:
        if isinstance(exc, HTTPError):
            transient = exc.code in (429, 500, 502, 503, 504)
        else:
            transient = isinstance(exc, TimeoutError) or "timed out" in str(exc).lower()
        if not transient:
            raise
        print("WARN: temporary BfDI download failure, retrying once", file=sys.stderr)
        return common.download(url)


def update(feed):
    name, kind = feed['id'], feed['type']
    urls = feed.get('urls') or [feed['url']]
    if not 1 <= len(urls) <= 2:
        raise ValueError('Expected one primary URL and at most one fallback')
    errors = []
    for url in urls:
        if urlparse(url).scheme != 'https':
            raise ValueError('Only HTTPS URLs allowed')
        try:
            payload = download_bfdi(url) if kind == 'bfdi' else common.download(url)
            if kind == 'kev':
                result = parse_kev(payload, url)
            else:
                try:
                    items = common.parse_feed(payload)
                except Exception:
                    if kind != 'bfdi':
                        raise
                    items = parse_bfdi_html(payload, url)
                fetched = datetime.now(timezone.utc)
                source_count = len(items)
                items = common.recent_items(items, fetched)
                start, end = common.berlin_window(fetched)
                result = {'feed': name, 'source': url,
                          'fetched_at': fetched.isoformat(timespec='seconds'),
                          'source_count': source_count, 'window_days': 3,
                          'window_start': start.isoformat(), 'window_end': end.isoformat(),
                          'count': len(items), 'items': items}
            common.write_json(common.OUT / (name + '.json'), result)
            print('OK:', name, 'count=', result['count'], 'source=', url)
            return
        except Exception as exc:
            errors.append(f'{url}: {type(exc).__name__}: {exc}')
    raise ValueError(' | '.join(errors))


def main():
    config = json.loads(common.CONFIG.read_text(encoding='utf-8'))
    bad = []
    for feed in config['feeds']:
        if feed.get('type', 'rss') == 'rss':
            continue
        if feed.get('manual_only', False):
            print('SKIP:', feed['id'], 'known inaccessible source, awaiting a new verified endpoint')
            continue
        try:
            update(feed)
        except Exception as exc:
            print(f'ERROR {feed["id"]}: {exc}', file=sys.stderr)
            bad.append(feed['id'])
    if bad:
        print('Supplemental sources not refreshed:', ', '.join(bad), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
