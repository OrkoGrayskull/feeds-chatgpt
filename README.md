# feeds-chatgpt

Öffentliche Nachrichten- und Behördenquellen als JSON für automatisierte Recherchen. Quellenkonfiguration: [feeds.json](feeds.json).

## Quellen

| JSON-Datei | Quelle |
| --- | --- |
| `data/security.json` | BSI/CERT-Bund – Sicherheitshinweise |
| `data/buergercert.json` | BSI – BürgerCERT |
| `data/cisa-kev.json` | CISA – Known Exploited Vulnerabilities |
| `data/bfdi.json` | BfDI – Pressemitteilungen |
| `data/curia.json` | CURIA – Pressemitteilungen |
| `data/eu-rechtsprechung.json` | EU-Rechtsprechung – CELLAR-Metadaten |
| `data/noyb.json` | noyb – Nachrichten |
| `data/eu-digital-strategy.json` | EU-Kommission – Digital Strategy |
| `data/edps-mastodon.json` | EDPS – Mastodon |
| `data/edpb.json` | EDPB – Nachrichten |
| `data/heise.json` | heise online – allgemeiner RSS |
| `data/golem.json` | Golem.de – allgemeiner RSS |

**Abdeckung:** Die Spiegel enthalten nur die jeweils verfügbaren oder konfigurierten Einträge. CURIA-Pressemitteilungen sind kein vollständiges Entscheidungsregister; EDPS-Mastodon und EDPB ersetzen kein vollständiges EDPS-Pressearchiv. Die allgemeinen heise- und Golem-Feeds werden ohne Themenfilter übernommen.

## Aktualisierung und Nutzung

[GitHub Actions](.github/workflows/update-feeds.yml) aktualisiert die JSON-Dateien täglich um **06:15 Uhr (Europe/Berlin)** und kann manuell gestartet werden. Geplante Läufe können sich verzögern oder ausfallen.

Abruf: `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json`

Die Daten enthalten Abrufzeitpunkt (`fetched_at`), Quelle und quellenspezifische Einträge. Der lesende Agent verwirft Spiegel, die **älter als acht Stunden** sind. Bei Abruffehlern bleibt der letzte funktionierende Datensatz erhalten; er darf nicht als aktuell behandelt werden.

Alle Inhalte stammen aus öffentlichen Drittquellen und müssen vor einer Veröffentlichung bei Bedarf anhand der Originalquellen geprüft werden.
