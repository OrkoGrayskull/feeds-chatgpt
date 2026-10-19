# feeds-chatgpt

Neutrale Sammlung öffentlich verfügbarer Datenquellen für automatisierte Recherchen. Die Konfiguration steht in [feeds.json](feeds.json). Quellen lassen sich um weitere Einträge erweitern.

## Aktive Datenquellen

| Datei | Quelle | Umfang |
| --- | --- | --- |
| `data/security.json` | BSI/CERT-Bund Sicherheitshinweise | Bis 100 RSS-Einträge |
| `data/buergercert.json` | BSI BürgerCERT | Bis 100 RSS-Einträge |
| `data/cisa-kev.json` | CISA Known Exploited Vulnerabilities | Vollständigen Katalog prüfen, jüngste 60 Tage veröffentlichen |
| `data/bfdi.json` | Offizielle BfDI-Presseübersicht | Datierte Pressemitteilungen samt Original-Link |
| `data/noyb.json` | noyb, öffentliche Nachrichten | Jüngste 50 RSS-Einträge, Beschreibungen auf 900 Zeichen gekürzt |
| `data/eu-digital-strategy.json` | EU-Kommission, Digital Strategy | Bis 20 RSS-Einträge, aktuell liefert die Quelle 10 |

Die BfDI-Datei umfasst nur die auf der Presseübersicht sichtbaren Mitteilungen, **nicht alle** Veröffentlichungen der Behörde.

## Unbestätigte Datenquellen

Der EDPS-RSS-Abruf antwortete bei beiden getesteten Endpunkten mit HTTP 403. Die Einträge bleiben zu Dokumentationszwecken in der Konfiguration, stehen aber auf `manual_only: true`, damit GitHub Actions die bekannten 403-Adressen nicht zweimal täglich nutzlos wiederholt. Es entsteht **keine** `data/edps.json`. Fehlende Daten dürfen nicht als »keine Meldungen« ausgelegt werden. Die Überwachung dieser Quelle muss bis zu einem erfolgreich getesteten neuen Abrufweg separat erfolgen.

## Abruf und Aktualität

Der Workflow [Update feeds](.github/workflows/update-feeds.yml) läuft täglich um 04:23 und 07:23 UTC sowie nach Änderungen an Skripten oder Feed-Konfigurationen. GitHub kann geplante Läufe verzögern.

Die Dateien werden unter `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json` veröffentlicht. Jeder Spiegel enthält `fetched_at` und die tatsächlich verwendete `source`-URL. Bei CISA sind zusätzlich `dateReleased`, `catalogVersion`, `catalog_count`, `window_start` und `window_days` vorhanden. `count` bezeichnet dort nur die veröffentlichten jüngeren Einträge.

**Fehlerverhalten:** Ein fehlgeschlagener Abruf überschreibt niemals den letzten funktionierenden Datensatz. Vor der Auswertung `fetched_at` prüfen und nicht aus einer alten Datei auf aktuelle Vollständigkeit schließen.

Alle Inhalte stammen aus öffentlichen Drittquellen und gelten als unvertrauenswürdige Daten. Keine privaten Quellen, Zugangsdaten oder personenbezogenen Zugangsinformationen in dieses öffentliche Repository übernehmen.
