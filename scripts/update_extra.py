#!/usr/bin/env python3
"""Publish supplemental public sources as compact dated JSON snapshots."""
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import update_feeds as common

common.MAX_BYTES = 6_000_000


def parse_kev(payload, url):
    catalog = json.loads(payload)
    records = catalog.get('vulnerabilities')
    if not isinstance(records, list) or not records or catalog.get('count') != len(records):
        raise ValueError('Invalid KEV catalog or mismatched count')
    if not catalog.get('catalogVersion') or not common.iso_date(catalog.get('dateReleased')):
        raise ValueError('Missing KEV catalog version or release date')
    cutoff = date.today() - timedelta(days=60)
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
        if added_date >= cutoff:
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
        'window_days': 60, 'window_start': cutoff.isoformat(),
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


def parse_bfdi_html(payload, source):
    # Conservative fallback: never infer dates from unrelated navigation markup.
    extractor = JSONLD()
    extractor.feed(payload.decode('utf-8', errors='replace'))
    result = []

    def walk(value):
        if isinstance(value, list):
            for sub in value:
                yield from walk(sub)
        elif isinstance(value, dict):
            yield value
            if '@graph' in value:
                yield from walk(value['@graph'])

    for blob in extractor.blobs:
        try:
            obj = json.loads(blob)
        except ValueError:
            continue
        for article in walk(obj):
            kind = article.get('@type', [])
            if isinstance(kind, str):
                kind = [kind]
            if not any(t in ('NewsArticle', 'Article', 'PressRelease') for t in kind):
                continue
            link = article.get('url') or article.get('mainEntityOfPage')
            if isinstance(link, dict):
                link = link.get('@id')
            link = urljoin(source, link or '')
            if urlparse(link).hostname not in ('bfdi.bund.de', 'www.bfdi.bund.de'):
                continue
            if '/Presse/' not in link:
                continue
            title = common.clean(article.get('headline', ''))
            published = common.iso_date(article.get('datePublished'))
            if title and published:
                result.append({'title': title, 'link': link, 'published': published,
                               'description': common.clean(article.get('description', ''))})
    if not result:
        sample = payload.decode('utf-8', errors='replace')[:8000]
        page_title = re.search(r'<title[^>]*>(.*?)</title>', sample, flags=re.I | re.S)
        print('Source diagnostic: HTML title =', common.clean(page_title.group(1))[:160] if page_title else '(none)', file=sys.stderr)
        print('Source diagnostic: dated strings =', re.findall(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', sample)[:5], file=sys.stderr)
        print('Source diagnostic: body text =', common.clean(sample)[:280], file=sys.stderr)
        full_html = payload.decode('utf-8', errors='replace')
        print('Source diagnostic: HTML bytes =', len(payload), file=sys.stderr)
        print('Source diagnostic: date count =', len(re.findall(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', full_html)), file=sys.stderr)
        print('Source diagnostic: first dates =', re.findall(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', full_html)[:10], file=sys.stderr)
        matches = list(re.finditer(r'href=["\x27]([^"\x27]*SharedDocs/Pressemitteilungen[^"\x27]*)', full_html, re.I))
        print('Source diagnostic: press links found =', len(matches), file=sys.stderr)
        for match in matches[:3]:
            print('Source diagnostic: excerpt =', common.clean(full_html[max(0,match.start()-350):match.end()+350])[:500], file=sys.stderr)
        raise ValueError('No dated press releases in structured HTML')
    return result[:100]


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
            payload = common.download(url)
            if kind == 'kev':
                result = parse_kev(payload, url)
            else:
                try:
                    items = common.parse_feed(payload)
                except Exception:
                    if kind != 'bfdi':
                        raise
                    items = parse_bfdi_html(payload, url)
                result = {'feed': name, 'source': url,
                          'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
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
