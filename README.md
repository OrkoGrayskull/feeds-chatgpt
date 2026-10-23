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
- **Atom-Datumsfelder:** `published` hat Vorrang für das Veröffentlichungsdatum, `updated` wird separat gespeichert. Fehlt `published`, wird `updated` nur als gekennzeichneter Fallback (`publication_date_source: updated_fallback`) verwendet. Eine spätere Bearbeitung mit vorhandenem `published` erzeugt deshalb keine künstlich neue Nachricht.
- **BSI:** Zwei amtliche Feeds. Als bewusste Ausnahme bleiben technische Sicherheitshinweise bis zu 72 Stunden im rollierenden Archiv, um eine optionale 72-Stunden-Rückschau zu ermöglichen. BürgerCERT wird auf drei Kalendertage begrenzt. Das Trunkierungsflag wird gegen das konfigurierte maximale RSS-Eintragslimit geprüft; historische Feed-Lücken bleiben möglich.
- **CISA KEV:** Der amtliche Gesamtkatalog wird bei der Verarbeitung validiert; gespeichert werden nur die in den letzten drei Berliner Kalendertagen neu hinzugefügten CVEs. `catalog_count` zählt den Gesamtkatalog und `count` die Treffer im aktuellen Ausschnitt.
- **CURIA und CELLAR:** Pressehinweise und CELLAR-Metadaten werden auf drei Berliner Kalendertage begrenzt. Dies ist keine vollständige Datenbank aller datenschutzrelevanten Entscheidungen; auch später indizierte ältere Entscheidungen können außerhalb des Fensters liegen. Originalentscheidungen sind gesondert zu prüfen.
- **BfDI, EDPB, EDPS:** BfDI-Presseübersicht, EDPB-Nachrichten und EDPS-Mastodon sind jeweils Teilmengen amtlicher Veröffentlichungen. BfDI bekommt bei einem temporären Timeout oder HTTP 429/5xx genau einen erneuten Abrufversuch, danach gilt der Quellfehler weiterhin als Fehler. Insbesondere EDPS-Mastodon ersetzt keine vollständige EDPS-Presseübersicht.
- **noyb und EU-Kommission:** Ergänzende Nachrichten- und Policy-Signale. Stellungnahmen, Beschwerden und Vorhaben nicht mit rechtskräftigen Feststellungen oder geltendem Recht verwechseln.
- **vzbv:** Drei RSS-Feeds für Pressemitteilungen, Urteile und digitale Themen; pro Datei höchstens die vom RSS gelieferten Einträge der letzten drei Kalendertage. Überschneidungen möglich, Urteile im Original prüfen.
- **heise und Golem:** Allgemeine redaktionelle Feeds ohne Themenfilter. Gespeichert werden die letzten drei Berliner Kalendertage; für die eigenständige Sieben-Tage-Recherche wird zusätzlich gezielt gesucht.
- **Bluesky:** Öffentliche Beiträge der letzten 24 Stunden. Suchbegriffe: `CVE`, `actively exploited`, `security advisory`, `Datenschutz`, `DSGVO`, `GDPR`, `data breach`, `Überwachung`, `surveillance`. Beobachtete Accounts: `noyb.eu`, `datenschutz.bsky.social`, `bleepingcomputer.com`, `ammir.bsky.social`, `responsible.fyi`, `eff.org`, `netzpolitik.org`, `ccc.de`, `infosec.skyfleet.blue`, `insecurestack.bsky.social`. Antworten und Reposts aus dem Account-Monitoring werden ausgeschlossen, doppelte Treffer zusammengeführt. Die Beiträge dienen als ergänzende Recherchehinweise, nicht als Primärbelege.
- **GitHub Advisory Database und NVD:** Abfragen ab Beginn des drittletzten Berliner Kalendertags. GitHub höchstens 100 aktuelle Advisories. NVD liest nach Ermittlung der Trefferanzahl gezielt die neuesten bis zu 200 CVEs, nicht mehr die ersten/ältesten 200. `total_results`, `truncated`, `start_index` und `selection` dokumentieren den begrenzten Ausschnitt; keine Vollständigkeitsgarantie.
- **EPSS:** Anreicherung für höchstens 50 unterschiedliche CVEs. Dafür werden zunächst Plätze für neu in KEV aufgenommene CVEs (bis zu 20), geprüfte GitHub Advisories (bis zu 15) und hoch bewertete NVD-CVEs (bis zu 15, CVSS ab 8,0) berücksichtigt. Ungenutzte Plätze werden quellenübergreifend neu vergeben; dieselbe CVE wird nur einmal angefragt. EPSS schätzt die Ausnutzungswahrscheinlichkeit und ist **kein Beleg für aktive Ausnutzung**.
- **Landesdatenschutzbehörden/DSK:** Sechs tägliche Quellen für Baden-Württemberg, Bayern, Berlin, Hamburg, Niedersachsen und DSK sind konfiguriert. Berlin und Niedersachsen werden vorerst über offizielle Mastodon-Posts erfasst, nicht über vollständige Pressearchive. Abrufe und Aktualität werden wie bei allen anderen Quellen geprüft. Relevante Ausfälle werden gegebenenfalls im betroffenen Bericht als Prüfhinweis genannt; andere Quellen und Recherchebereiche laufen unabhängig weiter.

## Automatische Prüfungen

Die offline ausführbaren Tests in `tests/test_feed_pipeline.py` prüfen Datumsgrenzen (einschließlich Sommer-/Winterzeit), RSS/Atom/RDF, BSI-Rückschau und Trunkierungsgrenze, optionale Fehler-Caches, KEV/CELLAR, NVD-Paginierung und EPSS-Kandidatenverteilung. Pull Requests durchlaufen `.github/workflows/test-feeds.yml`; der reguläre Aktualisierungsworkflow führt diese Tests vor dem Quellenabruf aus. Kein Test benötigt Internetzugriff.

## Aktualisierung und Nutzung

[GitHub Actions](.github/workflows/update-feeds.yml) sieht zwei **vollständige Aktualisierungen täglich um 05:45 und 07:45 Uhr (Europe/Berlin)** vor. Die beiden Cron-Einträge verwenden `timezone: Europe/Berlin`, sodass GitHub die Sommer-/Winterzeit berücksichtigt. Zusätzlich laufen **BSI-Zwischenabrufe** über den separaten UTC-Cron `10 0,3,9,12,15,18,21 * * *` (nur `security.json` und `buergercert.json`); sie aktualisieren keine anderen Quellen. Die Zeitangaben sind Sollzeiten: GitHub kann geplante Starts verzögern oder einzelne Läufe auslassen. Ein erfolgreicher BSI-Lauf ist daher **kein Beleg** für eine erfolgreiche vollständige Aktualisierung.

Manuelle Starts (`workflow_dispatch`) und Pushes auf `main`, die konfigurierte Dateien (Quellenkonfiguration, Skripte, Tests oder Aktualisierungsworkflow) verändern, lösen ebenfalls einen vollständigen Abruf aus. Eine reine README-Änderung löst keinen Abruf aus. Der Workflow protokolliert Ereignistyp, Cron-Ausdruck und gewählten Modus (`daily`, `security` oder `skip`). Unbekannte geplante Auslöser werden übersprungen und als Warnung markiert. Vor den Abrufen laufen Offline-Regressionstests; bei Fehlern verpflichtender Quellen wird der Lauf nach dem Versuch, andere Snapshots zu speichern, als fehlgeschlagen markiert. Fehler der optionalen Bluesky- und Schwachstellensignale blockieren die Pflichtquellen nicht. Konfiguration: [feeds.json](feeds.json). Für die tatsächliche Aktualität **Modus, einzelne Abrufschritte und `fetched_at` der benötigten JSON-Dateien** prüfen, nicht allein den grünen Gesamtstatus.

Dateien bevorzugt über die verbundene GitHub-App lesen, bei Fehler höchstens einmal über die öffentliche URL:

`https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json`

Der Tagesagent prüft **jede tatsächlich verwendete** GitHub-Datei einzeln auf Existenz, gültige JSON-Struktur, plausible Metadaten und `fetched_at` (heutiges Berliner Kalenderdatum und höchstens acht Stunden alt). Eine fehlende, fehlerhafte oder veraltete Datei wird nur als betroffene Quelle verworfen und bei wesentlicher Einschränkung als »nicht geprüft« vermerkt. **Es gibt keinen globalen Abbruch durch eine einzelne Quelle.** Die Recherche erfolgt in drei unabhängigen Bereichen: A1 IT-Sicherheit und A2 Datenschutz bilden gemeinsam eine Tagesbrief-Mail (A), sofern mindestens einer der beiden Bereiche ausreichend geprüft wurde; unzureichend geprüfte Bereiche werden klar gekennzeichnet. B ist ein eigenständiges gesellschaftliches Themenradar mit verpflichtender Sieben-Tage-Discovery und sendet nur bei einem qualifizierten Hauptthema eine separate Mail. B ist nicht von der Frische der A-Quellen abhängig. Ergänzende Dateien dürfen fehlen. Ein `count: 0` ist bei nachweislich erfolgreich aktualisierter, valider Quelle erlaubt. Für Nachrichten zählt das Veröffentlichungsdatum, nicht der Abrufzeitpunkt; bei Abruffehlern verbleibende alte Snapshots sind nicht aktuell. Bei optionalen RSS-Quellen werden ältere Cache-Einträge auch nach fehlgeschlagenem Abruf auf das Drei-Tage-Fenster begrenzt, ohne `fetched_at` zu erneuern.

Alle Snapshots sind Spiegel oder ergänzende Signale, keine unabhängigen Primärbelege. Relevante Aussagen vor Veröffentlichung anhand der Originalquellen prüfen. Keine Vollständigkeitsbehauptung allein aufgrund eines erfolgreichen Dateiabrufs.
