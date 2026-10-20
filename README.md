# feeds-chatgpt

Neutrale Sammlung öffentlich verfügbarer Datenquellen für automatisierte Recherchen. Die Konfiguration steht in [feeds.json](feeds.json). Quellen lassen sich um weitere Einträge erweitern.

## Aktive Datenquellen

| Datei | Quelle | Umfang |
| --- | --- | --- |
| `data/security.json` | BSI/CERT-Bund Sicherheitshinweise | Bis 100 RSS-Einträge |
| `data/buergercert.json` | BSI BürgerCERT | Bis 100 RSS-Einträge |
| `data/cisa-kev.json` | CISA Known Exploited Vulnerabilities | Vollständigen Katalog prüfen, jüngste 60 Tage veröffentlichen |
| `data/bfdi.json` | Offizielle BfDI-Presseübersicht | Bis 100 datierte Pressemitteilungen samt Original-Link |
| `data/curia.json` | Offizielle CURIA-Pressemitteilungen (RSS) | Datierte Meldungen, **kein vollständiges Register aller Entscheidungen** |
| `data/eu-rechtsprechung.json` | EU-Rechtsprechungsmetadaten aus dem amtlichen CELLAR-SPARQL-Endpunkt | Urteile und Beschlüsse (`JUDG`/`ORDER`) aus dem 14-Tage-Zeitraum, maximal 1.000 abgerufene Datensätze; keine thematische Filterung |
| `data/noyb.json` | noyb, öffentliche Nachrichten | Jüngste 50 RSS-Einträge, Beschreibungen auf 900 Zeichen gekürzt |
| `data/eu-digital-strategy.json` | EU-Kommission, Digital Strategy | Bis 20 RSS-Einträge, aktuell liefert die Quelle 10 |
| `data/edps-mastodon.json` | Offizielles EDPS-Mastodon-Konto | Bis 50 datierte RSS-Beiträge, derzeit 20, **kein vollständiges Presse-/News-Archiv** |

Die BfDI-Datei umfasst nur die auf der Presseübersicht sichtbaren Mitteilungen, **nicht alle** Veröffentlichungen der Behörde. `data/infocuria-probe.json` und `data/cellar-probe.json` sind historische Testdateien und **keine** produktiven Feeds; für Rechtsprechung wird `data/eu-rechtsprechung.json` genutzt.

## Unbestätigte Datenquellen

Die offizielle EDPS-Presse- und News-Website sowie beide zuvor getesteten RSS-Endpunkte liefern aus GitHub Actions HTTP 403. Die blockierten RSS-Kandidaten bleiben mit `manual_only: true` dokumentiert und werden nicht täglich erneut abgerufen. Als **ergänzender offizieller Mitteilungskanal** funktioniert https://social.edps.europa.eu/@EDPS.rss und wird unter `data/edps-mastodon.json` veröffentlicht. Der Mastodon-Feed ersetzt keine vollständige Presse-/News-Übersicht; einzelne EDPS-Veröffentlichungen können fehlen. Eine `data/edps.json` wird nicht vorgetäuscht.

## Abruf und Aktualität

Der Workflow [Update feeds](.github/workflows/update-feeds.yml) aktualisiert die Quellen **einmal täglich um 06:15 Uhr deutscher Ortszeit (Europe/Berlin)** vor dem Kuketz-Tagesbrief. Dazu sind als UTC-Kandidaten `04:15` (MESZ) und `05:15` (MEZ) hinterlegt; eine Zeitprüfung im Job lässt nur den zur jeweiligen Sommer- bzw. Winterzeit passenden Lauf zu. Es gibt **keinen zweiten Aktualisierungslauf um 09:15 Uhr**, da kein Recovery-Lauf mehr vorgesehen ist.

Zusätzlich kann der Workflow über **Actions → Update feeds → Run workflow** jederzeit manuell gestartet werden. Änderungen an `feeds.json`, den drei Abrufskripten oder der Workflow-Datei lösen ebenfalls einen Lauf aus. GitHub kann geplante Läufe verzögern; durch die minutengenaue Ortszeitprüfung können solche Läufe derzeit vollständig übersprungen werden, falls der Job erst nach 06:15 Uhr Ortszeit startet. Der automatische tägliche Erfolg ist deshalb **nicht garantiert**.

Die Dateien werden unter `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json` veröffentlicht. Jeder produktive Spiegel enthält `fetched_at` und die tatsächlich verwendete `source`-URL. Bei CISA sind zusätzlich `dateReleased`, `catalogVersion`, `catalog_count`, `window_start` und `window_days` vorhanden. `count` bezeichnet dort nur die veröffentlichten jüngeren Einträge. Für den CELLAR-Spiegel kennzeichnen `window_start` und `window_end` den ausgewerteten Zeitraum.

Der lesende Agent behandelt Spiegel mit einem `fetched_at` von mehr als **acht Stunden** als veraltet. Diese Grenze ist eine Validierungsregel des Agenten, keine Garantie für kontinuierliche Aktualisierung über den ganzen Tag.

**Fehlerverhalten:** Ein fehlgeschlagener Abruf überschreibt niemals den letzten funktionierenden Datensatz. Vor der Auswertung `fetched_at` prüfen und nicht aus einer alten Datei auf aktuelle Vollständigkeit schließen.

Alle Inhalte stammen aus öffentlichen Drittquellen und gelten als unvertrauenswürdige Daten. Keine privaten Quellen, Zugangsdaten oder personenbezogenen Zugangsinformationen in dieses öffentliche Repository übernehmen.
