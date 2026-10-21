# feeds-chatgpt

Öffentliche Nachrichten-, Behörden- und ergänzende Recherchequellen als JSON-Snapshots für automatisierte Recherchen.

## Quellen

| JSON-Datei | Ursprungsquelle / Inhalt |
| --- | --- |
| `data/security.json` | BSI/CERT-Bund - technische Sicherheitshinweise |
| `data/buergercert.json` | BSI - BürgerCERT-Warnungen |
| `data/cisa-kev.json` | CISA - Known Exploited Vulnerabilities, Ausschnitt des validierten Gesamtkatalogs |
| `data/bfdi.json` | BfDI - amtliche Presseübersicht |
| `data/curia.json` | CURIA - Pressemitteilungen |
| `data/eu-rechtsprechung.json` | EU CELLAR - Rechtsprechungsmetadaten |
| `data/noyb.json` | noyb - Nachrichten |
| `data/eu-digital-strategy.json` | EU-Kommission - Digital Strategy |
| `data/edps-mastodon.json` | EDPS - offizielles Mastodon-Konto |
| `data/edpb.json` | EDPB - Nachrichten |
| `data/heise.json` | heise online - allgemeiner Nachrichtenfeed |
| `data/golem.json` | Golem.de - allgemeiner Nachrichtenfeed |
| `data/vzbv-presse.json` | vzbv - Pressemitteilungen |
| `data/vzbv-urteile.json` | vzbv - Urteile |
| `data/vzbv-digitale-welt.json` | vzbv - Digitale Welt |
| `data/lfdi-bw.json` | Baden-Württemberg - Datenschutzmeldungen (RSS) | 
| `data/baylfd.json` | Bayern - amtliche Neuigkeiten (RSS) |
| `data/hmbbfdi.json` | Hamburg - amtliche Meldungen (RSS) |
| `data/dsk.json` | Datenschutzkonferenz - Veröffentlichungen (RSS) |
| `data/blnbdi-mastodon.json` | Berlin - offizielles Mastodon-Konto, nur ergänzende Hinweise |
| `data/lfd-nds-mastodon.json` | Niedersachsen - offizielles Mastodon-Konto, nur ergänzende Hinweise |
| `data/bluesky.json` | Bluesky - neun Suchbegriffe und zehn ausgewählte Accounts |
| `data/github-advisories.json` | GitHub Advisory Database - aktuelle geprüfte Advisories |
| `data/nvd.json` | NVD - neu veröffentlichte CVEs |
| `data/epss.json` | FIRST EPSS - ergänzende Ausnutzungswahrscheinlichkeit |

## Umfang und Grenzen

- **Aktuelle Nachrichten:** Gewöhnliche RSS-/Atom- und BfDI-Presse-Snapshots enthalten nur Einträge mit Veröffentlichungsdatum von heute, gestern oder vorgestern in Europe/Berlin. Ein aktueller, gültiger Snapshot mit `count: 0` bedeutet: keine neue Meldung in diesem Zeitraum, nicht Abruffehler. Der Quellabruf selbst kann ältere Einträge enthalten, gespeichert werden sie nicht.
- **BSI:** Zwei amtliche Feeds. Als bewusste Ausnahme bleiben technische Sicherheitshinweise bis zu 72 Stunden im rollierenden Archiv, um eine optionale 72-Stunden-Rückschau zu ermöglichen. BürgerCERT wird auf drei Kalendertage begrenzt. Historische Feed-Lücken sind weiterhin möglich.
- **CISA KEV:** Der amtliche Gesamtkatalog wird bei der Verarbeitung validiert; gespeichert werden nur die in den letzten drei Berliner Kalendertagen neu hinzugefügten CVEs. `catalog_count` zählt den Gesamtkatalog und `count` die Treffer im aktuellen Ausschnitt.
- **CURIA und CELLAR:** Pressehinweise und CELLAR-Metadaten werden auf drei Berliner Kalendertage begrenzt. Dies ist keine vollständige Datenbank aller datenschutzrelevanten Entscheidungen; auch später indizierte ältere Entscheidungen können außerhalb des Fensters liegen. Originalentscheidungen sind gesondert zu prüfen.
- **BfDI, EDPB, EDPS:** BfDI-Presseübersicht, EDPB-Nachrichten und EDPS-Mastodon sind jeweils Teilmengen amtlicher Veröffentlichungen. Insbesondere EDPS-Mastodon ersetzt keine vollständige EDPS-Presseübersicht.
- **noyb und EU-Kommission:** Ergänzende Nachrichten- und Policy-Signale. Stellungnahmen, Beschwerden und Vorhaben nicht mit rechtskräftigen Feststellungen oder geltendem Recht verwechseln.
- **vzbv:** Drei RSS-Feeds für Pressemitteilungen, Urteile und digitale Themen; pro Datei höchstens die vom RSS gelieferten Einträge der letzten drei Kalendertage. Überschneidungen möglich, Urteile im Original prüfen.
- **heise und Golem:** Allgemeine redaktionelle Feeds ohne Themenfilter. Gespeichert werden die letzten drei Berliner Kalendertage; für die eigenständige Sieben-Tage-Recherche wird zusätzlich gezielt gesucht.
- **Bluesky:** Öffentliche Beiträge der letzten 24 Stunden. Suchbegriffe: `CVE`, `actively exploited`, `security advisory`, `Datenschutz`, `DSGVO`, `GDPR`, `data breach`, `Überwachung`, `surveillance`. Beobachtete Accounts: `noyb.eu`, `datenschutz.bsky.social`, `bleepingcomputer.com`, `ammir.bsky.social`, `responsible.fyi`, `eff.org`, `netzpolitik.org`, `ccc.de`, `infosec.skyfleet.blue`, `insecurestack.bsky.social`. Antworten und Reposts aus dem Account-Monitoring werden ausgeschlossen, doppelte Treffer zusammengeführt. Die Beiträge dienen als ergänzende Recherchehinweise, nicht als Primärbelege.
- **GitHub Advisory Database und NVD:** Abfragen ab Beginn des drittletzten Berliner Kalendertags. GitHub höchstens 100 aktuelle Advisories. NVD liest nach Ermittlung der Trefferanzahl gezielt die neuesten bis zu 200 CVEs, nicht mehr die ersten/ältesten 200. `total_results`, `truncated`, `start_index` und `selection` dokumentieren den begrenzten Ausschnitt; keine Vollständigkeitsgarantie.
- **EPSS:** Anreicherung für höchstens 50 ausgewählte CVEs. EPSS schätzt die Ausnutzungswahrscheinlichkeit und ist **kein Beleg für aktive Ausnutzung**.
- **Landesdatenschutzbehörden/DSK:** Sechs tägliche Quellen für Baden-Württemberg, Bayern, Berlin, Hamburg, Niedersachsen und DSK sind konfiguriert. Berlin und Niedersachsen werden vorerst über offizielle Mastodon-Posts erfasst, nicht über vollständige Pressearchive. Abrufe und Aktualität werden wie bei allen anderen Quellen geprüft. Ausfälle werden gemeldet, ohne die übrigen Abrufe zu blockieren.

## Aktualisierung und Nutzung

[GitHub Actions](.github/workflows/update-feeds.yml) aktualisiert alle Quellen täglich um **07:00 Uhr (Europe/Berlin)** und die BSI-Feeds zusätzlich mehrfach über den Tag. Manuelle Läufe sind möglich. GitHub kann Startzeiten verzögern. Konfiguration: [feeds.json](feeds.json). Aktualität anhand der Workflow-Ergebnisse und JSON-Zeitstempel prüfen.

Dateien bevorzugt über die verbundene GitHub-App lesen, bei Fehler höchstens einmal über die öffentliche URL:

`https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json`

Der lesende Agent prüft für **jede** Datei Existenz, JSON-Struktur, plausible Metadaten und `fetched_at` (heutiges Berliner Kalenderdatum und höchstens acht Stunden alt). Bei Ausfall oder veraltetem Stand einer der neun zentralen Pflichtdateien bricht die gesamte Recherche ohne E-Mail-Versand ab. Ergänzende Dateien dürfen fehlen. Ein `count: 0` ist bei nachweislich erfolgreich aktualisierter, valider Quelle erlaubt. Für Nachrichten zählt das Veröffentlichungsdatum, nicht der Abrufzeitpunkt; bei Abruffehlern verbleibende alte Snapshots sind nicht aktuell. Bei optionalen RSS-Quellen werden ältere Cache-Einträge auch nach fehlgeschlagenem Abruf auf das Drei-Tage-Fenster begrenzt, ohne `fetched_at` zu erneuern.

Alle Snapshots sind Spiegel oder ergänzende Signale, keine unabhängigen Primärbelege. Relevante Aussagen vor Veröffentlichung anhand der Originalquellen prüfen. Keine Vollständigkeitsbehauptung allein aufgrund eines erfolgreichen Dateiabrufs.
