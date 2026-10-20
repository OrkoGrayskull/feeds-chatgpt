# feeds-chatgpt

Öffentliche Nachrichten-, Behörden- und ergänzende Recherchequellen als JSON-Snapshots für den Kuketz-Tagesbrief und das Themenradar.

## Quellen und Status

**Statusdefinitionen:** »Snapshot vorhanden« bedeutet, dass eine JSON-Datei im Repository tatsächlich nachgewiesen wurde, **nicht**, dass der aktuelle Lauf erfolgreich oder der Inhalt vollständig ist. »Integration offen« bedeutet, dass Skript und Workflow konfiguriert sind, aber noch kein erfolgreicher API-Abruf mit erzeugtem Snapshot bestätigt wurde.

| JSON-Datei | Ursprungsquelle / Inhalt | Status |
| --- | --- | --- |
| `data/security.json` | BSI/CERT-Bund - technische Sicherheitshinweise | Snapshot vorhanden |
| `data/buergercert.json` | BSI - BürgerCERT-Warnungen | Snapshot vorhanden |
| `data/cisa-kev.json` | CISA - Known Exploited Vulnerabilities, Ausschnitt des validierten Gesamtkatalogs | Snapshot vorhanden |
| `data/bfdi.json` | BfDI - amtliche Presseübersicht | Snapshot vorhanden |
| `data/curia.json` | CURIA - Pressemitteilungen | Snapshot vorhanden |
| `data/eu-rechtsprechung.json` | EU CELLAR - Rechtsprechungsmetadaten | Snapshot vorhanden |
| `data/noyb.json` | noyb - Nachrichten | Snapshot vorhanden |
| `data/eu-digital-strategy.json` | EU-Kommission - Digital Strategy | Snapshot vorhanden |
| `data/edps-mastodon.json` | EDPS - offizielles Mastodon-Konto | Snapshot vorhanden |
| `data/edpb.json` | EDPB - Nachrichten | Snapshot vorhanden |
| `data/heise.json` | heise online - allgemeiner Nachrichtenfeed | Snapshot vorhanden |
| `data/golem.json` | Golem.de - allgemeiner Nachrichtenfeed | Snapshot vorhanden |
| `data/bluesky.json` | Bluesky - neun Suchbegriffe und zehn ausgewählte Accounts | Snapshot vorhanden |
| `data/github-advisories.json` | GitHub Advisory Database - aktuelle geprüfte Advisories | **Integration offen** |
| `data/nvd.json` | NVD - neu veröffentlichte CVEs | **Integration offen** |
| `data/epss.json` | FIRST EPSS - ergänzende Ausnutzungswahrscheinlichkeit | **Integration offen** |

Die Statusangaben beruhen auf einer Prüfung der Repository-Dateien am **20.10.2026**. Sie sind keine automatisch aktualisierte Laufzeitüberwachung. Bei den drei neuen Schwachstellenquellen ist bislang **kein produktiver JSON-Snapshot nachgewiesen**. Erst nach API-Prüfung, erfolgreicher Aktualisierung und Integrationstest darf ihre erweiterte Abdeckung als bestätigt gelten.

## Umfang und Grenzen

- **BSI:** Zwei amtliche RSS-Feeds als JSON gespiegelt. Die Auswahl kann auf die letzten 100 Einträge je Feed begrenzt sein.
- **CISA KEV:** Amtlicher Gesamtkatalog wird bei der Verarbeitung validiert, im JSON stehen die Einträge der letzten 60 Tage. `catalog_count` bezeichnet die Größe des vollständigen Katalogs, `count` die Zahl im Ausschnitt.
- **CURIA und CELLAR:** Pressemitteilungen und Metadaten ergänzen sich, sind aber kein vollständiges Verzeichnis aller datenschutzrelevanten Entscheidungen. Originalentscheidungen sind gesondert zu prüfen.
- **BfDI, EDPB, EDPS:** BfDI-Presseübersicht, EDPB-Nachrichten und EDPS-Mastodon sind jeweils Teilmengen amtlicher Veröffentlichungen. Insbesondere EDPS-Mastodon ersetzt keine vollständige EDPS-Presseübersicht.
- **noyb und EU-Kommission:** Ergänzende Nachrichten- und Policy-Signale. Stellungnahmen, Beschwerden und Vorhaben nicht mit rechtskräftigen Feststellungen oder geltendem Recht verwechseln.
- **heise und Golem:** Allgemeine redaktionelle Feeds ohne Themenfilter, nicht notwendigerweise vollständige Sieben-Tage-Archive.
- **Bluesky:** Öffentliche Posts aus einem 24-Stunden-Fenster, neun Suchbegriffe (einschließlich `Überwachung` und `surveillance`) sowie zehn Accounts. Account-Antworten und Reposts werden ausgeschlossen, Treffer dedupliziert. Nur ergänzende Hinweise für **A und B**, keine Primärbelege.
- **GitHub Advisory Database und NVD:** Vorgesehene begrenzte Abfrage der letzten 72 Stunden. GitHub maximal 100 Ergebnisse, NVD maximal 200 Ergebnisse je Lauf, keine Vollständigkeitsgarantie bei größeren Ergebnismengen. **Noch nicht erfolgreich end-to-end verifiziert.**
- **EPSS:** Vorgesehene Anreicherung für höchstens 50 ausgewählte CVEs. EPSS schätzt die Ausnutzungswahrscheinlichkeit und ist **kein Beleg für aktive Ausnutzung**. **Noch nicht erfolgreich end-to-end verifiziert.**

## Aktualisierung und Nutzung

[GitHub Actions](.github/workflows/update-feeds.yml) ist für eine tägliche Aktualisierung um **06:15 Uhr (Europe/Berlin)** konfiguriert und kann manuell ausgelöst werden. Geplante Läufe können sich verzögern oder ausfallen. Die Quellenkonfiguration steht in [feeds.json](feeds.json), zusätzliche Quellen werden über eigene Skripte aktualisiert.

Dateien bevorzugt über die verbundene GitHub-App lesen, bei Fehler höchstens einmal über die öffentliche URL:

`https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json`

Der lesende Agent prüft für **jede** Datei die tatsächliche Existenz, JSON-Struktur, plausible Metadaten und `fetched_at` (**höchstens acht Stunden alt**). Für die Nachrichtenauswahl zählt das Veröffentlichungsdatum des Eintrags, nicht der technische Abrufzeitpunkt. Bei Fehlern bleibt gegebenenfalls ein älterer Snapshot bestehen, der nicht als aktuell ausgegeben werden darf. Optionale Quellen dürfen Pflichtquellen, andere Berichtsteile oder den E-Mail-Versand nicht blockieren.

Alle Snapshots sind Spiegel oder ergänzende Signale, keine unabhängigen Primärbelege. Relevante Aussagen vor Veröffentlichung anhand der Originalquellen prüfen. Keine Vollständigkeitsbehauptung allein aufgrund eines erfolgreichen Dateiabrufs.
