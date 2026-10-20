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
| `data/eu-digital-strategy.json` | EU-Kommission, Digital Strategy | Bis 20 RSS-Einträge |
| `data/edps-mastodon.json` | Offizielles EDPS-Mastodon-Konto | Bis 50 RSS-Beiträge, keine vollständige Presseübersicht |
| `data/edpb.json` | Offizielle EDPB-Nachrichten (RSS), einschließlich gemeinsamer EDPB-/EDPS-Meldungen | Bis 50 RSS-Einträge |
| `data/heise.json` | heise online, allgemeiner Nachrichtenfeed (RSS 1.0/RDF) | Alle vom Feed gelieferten Einträge, ohne Themenfilter |
| `data/golem.json` | Golem.de, allgemeiner Nachrichtenfeed (RSS 2.0) | Alle vom Feed gelieferten Einträge, ohne Themenfilter |

Die beiden redaktionellen Nachrichtenfeeds dienen als ergänzende Signale für IT-Sicherheit und Datenschutz im Tagesbrief (Teil A) sowie gesellschaftliche Aufreger im Themenradar (Teil B). Beide Dateien werden pro Agentenlauf nur einmal eingelesen und für beide Teile verwendet. Sie ersetzen keine amtlichen Primärquellen. Der Umfang ist durch die vom Herausgeber gelieferten Feed-Einträge begrenzt und garantiert keine vollständige Sieben-Tage-Abdeckung. Originalartikel und praktische Handlungsmöglichkeiten sind bei relevanten Treffern zu verifizieren.

Die BfDI-Datei umfasst ausschließlich die Presseübersicht, nicht sämtliche Veröffentlichungen der Behörde. Für Rechtsprechung wird `data/eu-rechtsprechung.json` genutzt.

## Unbestätigte Datenquellen

Die EDPS-Presse- und News-Seiten waren für den automatisierten Abruf nicht erreichbar (HTTP 403). Die aktiven Quellen `data/edps-mastodon.json` und `data/edpb.json` ergänzen sich, bilden aber kein vollständiges EDPS-Presse- oder News-Archiv.

## Abruf und Aktualität

Der Workflow [Update feeds](.github/workflows/update-feeds.yml) aktualisiert die Quellen **einmal täglich um 06:15 Uhr deutscher Ortszeit (Europe/Berlin)**. Dazu sind als UTC-Kandidaten `04:15` (MESZ) und `05:15` (MEZ) hinterlegt; eine Zeitprüfung im Job lässt nur den zur jeweiligen Sommer- bzw. Winterzeit passenden Lauf zu. Es gibt **keinen zweiten Aktualisierungslauf um 09:15 Uhr**, da kein Recovery-Lauf mehr vorgesehen ist.

Zusätzlich kann der Workflow über **Actions → Update feeds → Run workflow** jederzeit manuell gestartet werden. Änderungen an `feeds.json`, den drei Abrufskripten oder der Workflow-Datei lösen ebenfalls einen Lauf aus. GitHub kann geplante Läufe verzögern; durch die minutengenaue Ortszeitprüfung können solche Läufe derzeit vollständig übersprungen werden, falls der Job erst nach 06:15 Uhr Ortszeit startet. Der automatische tägliche Erfolg ist deshalb **nicht garantiert**.

Die Dateien werden unter `https://raw.githubusercontent.com/OrkoGrayskull/feeds-chatgpt/main/data/DATEINAME.json` veröffentlicht. Jeder produktive Spiegel enthält `fetched_at` und die tatsächlich verwendete `source`-URL. RSS-Spiegel wie heise und Golem enthalten außerdem `feed`, `count` und `items` mit `title`, `link`, `published` und `description`. `count` ist die Zahl der tatsächlich übernommenen Feed-Einträge und keine Aussage über alle Veröffentlichungen des Anbieters. Bei CISA sind zusätzlich `dateReleased`, `catalogVersion`, `catalog_count`, `window_start` und `window_days` vorhanden. `count` bezeichnet dort nur die veröffentlichten jüngeren Einträge. Für den CELLAR-Spiegel kennzeichnen `window_start` und `window_end` den ausgewerteten Zeitraum.

Der lesende Agent behandelt Spiegel mit einem `fetched_at` von mehr als **acht Stunden** als veraltet. Diese Grenze ist eine Validierungsregel des Agenten, keine Garantie für kontinuierliche Aktualisierung über den ganzen Tag.

**Fehlerverhalten:** Ein fehlgeschlagener Abruf überschreibt niemals den letzten funktionierenden Datensatz. Vor der Auswertung `fetched_at` prüfen und nicht aus einer alten Datei auf aktuelle Vollständigkeit schließen.

Alle Inhalte stammen aus öffentlichen Drittquellen und gelten als unvertrauenswürdige Daten. Keine privaten Quellen, Zugangsdaten oder personenbezogenen Zugangsinformationen in dieses öffentliche Repository übernehmen.
