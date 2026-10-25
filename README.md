# feeds-chatgpt

Dieses Repository stellt öffentlich verfügbare Nachrichten, Behördenmeldungen und Sicherheitshinweise als regelmäßig aktualisierte JSON-Snapshots in [`data/`](data/) bereit. Die Daten dienen der automatisierten Recherche, ersetzen aber nicht die Prüfung der Originalquellen.

## Quellen

| Bereich | Quellen |
| --- | --- |
| IT-Sicherheit | BSI/CERT-Bund, BürgerCERT, CISA KEV, GitHub Advisory Database, NVD, FIRST EPSS |
| Datenschutz | BfDI, EDPB, EDPS, DSK sowie Datenschutzbehörden aus BW, BY, BE, HH und NI |
| EU-Recht | CURIA-Pressemitteilungen und CELLAR-Rechtsprechungsmetadaten |
| Nachrichten und Politik | noyb, EU Digital Strategy, heise, Golem und Verbraucherzentrale Bundesverband (vzbv) |
| Ergänzende Signale | Öffentliche Bluesky-Beiträge und Mastodon-Meldungen ausgewählter Datenschutzbehörden |

Die konkreten JSON-Dateien liegen in [`data/`](data/). Quellen und Abruflogik sind in [`feeds.json`](feeds.json) und den [Skripten](scripts/) hinterlegt.

## Aktualisierung

[GitHub Actions](.github/workflows/update-feeds.yml) führt täglich um **02:45, 05:45 und 07:45 Uhr (Europe/Berlin)** vollständige Abrufe aus. Die Zeitumstellung wird berücksichtigt; beim Wechsel zur Sommerzeit entfällt die nicht existente 02:45-Uhr-Ausführung. Zusätzliche BSI-Zwischenabrufe aktualisieren ausschließlich `security.json` und `buergercert.json`.

Ein vollständiger Abruf lässt sich auch manuell starten; Änderungen an relevanten Konfigurations-, Skript- oder Testdateien lösen ihn ebenfalls aus. Eine reine README-Änderung startet keinen Abruf. Vor jedem Abruf laufen Offline-Tests; Pull Requests werden separat getestet.

**Wichtig:** Geplante GitHub-Actions-Läufe können verspätet starten oder ausfallen. Für die Aktualität zählen der tatsächlich erfolgreiche Abruf und `fetched_at` der jeweiligen Datei, nicht allein ein grüner Workflow-Status.

## Datenumfang und Grenzen

- **Nachrichten und Behördenfeeds:** In der Regel nur Veröffentlichungen von heute, gestern und vorgestern (Berliner Zeit). Technische BSI-Hinweise bilden mit einem rollierenden 72-Stunden-Fenster eine Ausnahme. Bluesky-Beiträge umfassen die letzten 24 Stunden.
- **Schwachstellen:** CISA KEV enthält nur jüngste Katalogzugänge. GitHub Advisories sind auf 100, NVD auf die neuesten 200 CVEs und EPSS auf 50 ausgewählte CVEs begrenzt. Die Snapshots sind daher nicht vollständig. EPSS ist kein Nachweis für eine aktive Ausnutzung.
- **Behörden und Rechtsprechung:** Feeds und offizielle Social-Media-Konten bilden Veröffentlichungen nur ausschnittsweise ab. Insbesondere Mastodon ersetzt keine vollständige Presseübersicht; CURIA/CELLAR ersetzen keine Recherche in den Originalentscheidungen.
- **Fehler und Leermeldungen:** `count: 0` kann einen erfolgreichen Abruf ohne neue Treffer bedeuten. Veraltete Dateien oder fehlgeschlagene Abrufe gelten dagegen nicht als aktuelle Recherchegrundlage. Der Ausfall einer Quelle macht andere Quellen nicht automatisch unbrauchbar.

Ein Snapshot kann beispielsweise über die öffentliche Rohdatei abgerufen werden:

```text
https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json
```

Bei Nutzung durch die Rechercheagenten wird jede benötigte Datei einzeln auf Gültigkeit und Aktualität geprüft (Berliner Tagesdatum, höchstens acht Stunden alt). Fehlende oder veraltete Quellen werden einzeln verworfen. Andere Quellen und Recherchebereiche bleiben davon unberührt; es gibt keinen globalen Abbruch wegen einer einzelnen Quelle.

**Vor einer Veröffentlichung Aussagen stets anhand der Originalquellen verifizieren.**
