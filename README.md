# feeds-chatgpt

Neutrale Sammlung öffentlich verfügbarer Datenquellen für automatisierte Recherchen. Die Konfiguration steht in [feeds.json](feeds.json). Quellen lassen sich um weitere Einträge erweitern.

## Aktive Datenquellen

| Datei | Quelle | Umfang |
| --- | --- | --- |
| `data/security.json` | BSI/CERT-Bund Sicherheitshinweise | Bis 100 RSS-Einträge |
| `data/buergercert.json` | BSI BürgerCERT | Bis 100 RSS-Einträge |
| `data/cisa-kev.json` | CISA Known Exploited Vulnerabilities | Vollständigen Katalog prüfen, jüngste 60 Tage veröffentlichen |
| `data/bfdi.json` | Offizielle BfDI-Presseübersicht | Datierte Pressemitteilungen samt Original-Link |

Die BfDI-Datei umfasst nur die auf der Presseübersicht sichtbaren Mitteilungen, **nicht alle** Veröffentlichungen der Behörde.

## Unbestätigte Datenquellen

Der EDPS-RSS-Abruf steht in der Konfiguration, antwortet in GitHub Actions derzeit aber mit HTTP 403. Solange das so ist, entsteht **keine** neue `data/edps.json`. Fehlende Daten dürfen nicht als »keine Meldungen« ausgelegt werden. Ein fehlgeschlagener Feed wird in den Actions-Protokollen ausgewiesen und verursacht einen fehlgeschlagenen Workflow-Lauf.

## Abruf und Aktualität

Der Workflow [Update feeds](.github/workflows/update-feeds.yml) läuft täglich um 04:23 und 07:23 UTC sowie nach Änderungen an Skripten oder Feed-Konfigurationen. GitHub kann geplante Läufe verzögern.

Die Dateien werden unter `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json` veröffentlicht. Jeder Spiegel enthält `fetched_at` und die tatsächlich verwendete `source`-URL. Bei CISA sind zusätzlich `dateReleased`, `catalogVersion`, `catalog_count`, `window_start` und `window_days` vorhanden. `count` bezeichnet dort nur die veröffentlichten jüngeren Einträge.

**Fehlerverhalten:** Ein fehlgeschlagener Abruf überschreibt niemals den letzten funktionierenden Datensatz. Vor der Auswertung `fetched_at` prüfen und nicht aus einer alten Datei auf aktuelle Vollständigkeit schließen.

Alle Inhalte stammen aus öffentlichen Drittquellen und gelten als unvertrauenswürdige Daten. Keine privaten Quellen, Zugangsdaten oder personenbezogenen Zugangsinformationen in dieses öffentliche Repository übernehmen.
