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
| `data/edps-mastodon.json` | Offizielles EDPS-Mastodon-Konto | Bis 50 datierte RSS-Beiträge, derzeit 20, **kein vollständiges Presse-/News-Archiv** |

Die BfDI-Datei umfasst nur die auf der Presseübersicht sichtbaren Mitteilungen, **nicht alle** Veröffentlichungen der Behörde.

## Unbestätigte Datenquellen

Die offizielle EDPS-Presse- und News-Website sowie beide zuvor getesteten RSS-Endpunkte liefern aus GitHub Actions HTTP 403. Die blockierten RSS-Kandidaten bleiben mit `manual_only: true` dokumentiert und werden nicht täglich erneut abgerufen. Als **ergänzender offizieller Mitteilungskanal** funktioniert https://social.edps.europa.eu/@EDPS.rss und wird unter `data/edps-mastodon.json` veröffentlicht. Der Mastodon-Feed ersetzt keine vollständige Presse-/News-Übersicht; einzelne EDPS-Veröffentlichungen können fehlen. Eine `data/edps.json` wird nicht vorgetäuscht.

## Abruf und Aktualität

Der Workflow [Update feeds](.github/workflows/update-feeds.yml) läuft täglich um 04:23 und 07:23 UTC sowie nach Änderungen an Skripten oder Feed-Konfigurationen. GitHub kann geplante Läufe verzögern.

Die Dateien werden unter `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json` veröffentlicht. Jeder Spiegel enthält `fetched_at` und die tatsächlich verwendete `source`-URL. Bei CISA sind zusätzlich `dateReleased`, `catalogVersion`, `catalog_count`, `window_start` und `window_days` vorhanden. `count` bezeichnet dort nur die veröffentlichten jüngeren Einträge.

**Fehlerverhalten:** Ein fehlgeschlagener Abruf überschreibt niemals den letzten funktionierenden Datensatz. Vor der Auswertung `fetched_at` prüfen und nicht aus einer alten Datei auf aktuelle Vollständigkeit schließen.

Alle Inhalte stammen aus öffentlichen Drittquellen und gelten als unvertrauenswürdige Daten. Keine privaten Quellen, Zugangsdaten oder personenbezogenen Zugangsinformationen in dieses öffentliche Repository übernehmen.
