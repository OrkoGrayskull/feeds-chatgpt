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

- **BSI:** Zwei amtliche RSS-Feeds als JSON gespiegelt. Die Auswahl kann auf die letzten 100 Einträge je Feed begrenzt sein.
- **CISA KEV:** Amtlicher Gesamtkatalog wird bei der Verarbeitung validiert, im JSON stehen die Einträge der letzten 60 Tage. `catalog_count` bezeichnet die Größe des vollständigen Katalogs, `count` die Zahl im Ausschnitt.
- **CURIA und CELLAR:** Pressemitteilungen und Metadaten ergänzen sich, sind aber kein vollständiges Verzeichnis aller datenschutzrelevanten Entscheidungen. Originalentscheidungen sind gesondert zu prüfen.
- **BfDI, EDPB, EDPS:** BfDI-Presseübersicht, EDPB-Nachrichten und EDPS-Mastodon sind jeweils Teilmengen amtlicher Veröffentlichungen. Insbesondere EDPS-Mastodon ersetzt keine vollständige EDPS-Presseübersicht.
- **noyb und EU-Kommission:** Ergänzende Nachrichten- und Policy-Signale. Stellungnahmen, Beschwerden und Vorhaben nicht mit rechtskräftigen Feststellungen oder geltendem Recht verwechseln.
- **heise und Golem:** Allgemeine redaktionelle Feeds ohne Themenfilter, nicht notwendigerweise vollständige Sieben-Tage-Archive.
- **Bluesky:** Öffentliche Beiträge der letzten 24 Stunden. Suchbegriffe: `CVE`, `actively exploited`, `security advisory`, `Datenschutz`, `DSGVO`, `GDPR`, `data breach`, `Überwachung`, `surveillance`. Beobachtete Accounts: `noyb.eu`, `datenschutz.bsky.social`, `bleepingcomputer.com`, `ammir.bsky.social`, `responsible.fyi`, `eff.org`, `netzpolitik.org`, `ccc.de`, `infosec.skyfleet.blue`, `insecurestack.bsky.social`. Antworten und Reposts aus dem Account-Monitoring werden ausgeschlossen, doppelte Treffer zusammengeführt. Die Beiträge dienen als ergänzende Recherchehinweise, nicht als Primärbelege.
- **GitHub Advisory Database und NVD:** Begrenzte Abfrage der letzten 72 Stunden. GitHub maximal 100 Ergebnisse, NVD maximal 200 Ergebnisse je Lauf, keine Vollständigkeitsgarantie bei größeren Ergebnismengen.
- **EPSS:** Anreicherung für höchstens 50 ausgewählte CVEs. EPSS schätzt die Ausnutzungswahrscheinlichkeit und ist **kein Beleg für aktive Ausnutzung**.

- **Landesdatenschutzbehörden/DSK:** Sechs neue optionale Signalfeeds für Baden-Württemberg, Bayern, Berlin, Hamburg, Niedersachsen und DSK sind konfiguriert. Berlin und Niedersachsen werden vorerst über offizielle Mastodon-Posts erfasst, nicht über vollständige Pressearchive. Ein erfolgreicher produktiver Abruf aller sechs Quellen ist noch nicht bestätigt. Fehler dürfen die bisherigen Feeds nicht blockieren.

## Aktualisierung und Nutzung

[GitHub Actions](.github/workflows/update-feeds.yml) ist für eine tägliche Aktualisierung um **06:15 Uhr (Europe/Berlin)** konfiguriert und kann manuell ausgelöst werden. Geplante Läufe können sich verzögern oder ausfallen. Die Quellenkonfiguration steht in [feeds.json](feeds.json), zusätzliche Quellen werden über eigene Skripte aktualisiert. Ob eine Datei erfolgreich aktualisiert wurde, ist anhand des jeweiligen Workflow-Laufs und ihres Zeitstempels zu prüfen.

Dateien bevorzugt über die verbundene GitHub-App lesen, bei Fehler höchstens einmal über die öffentliche URL:

`https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json`

Der lesende Agent prüft für **jede** Datei die tatsächliche Existenz, JSON-Struktur, plausible Metadaten und `fetched_at` (**höchstens acht Stunden alt**). Für die Nachrichtenauswahl zählt das Veröffentlichungsdatum des Eintrags, nicht der technische Abrufzeitpunkt. Bei Fehlern bleibt gegebenenfalls ein älterer Snapshot bestehen, der nicht als aktuell ausgegeben werden darf. Optionale Quellen dürfen Pflichtquellen, andere Berichtsteile oder den E-Mail-Versand nicht blockieren.

Alle Snapshots sind Spiegel oder ergänzende Signale, keine unabhängigen Primärbelege. Relevante Aussagen vor Veröffentlichung anhand der Originalquellen prüfen. Keine Vollständigkeitsbehauptung allein aufgrund eines erfolgreichen Dateiabrufs.
