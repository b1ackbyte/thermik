<p align="center">
<img src="thermik.png" alt="Thermik" width="200">
</p>

# Thermik

Home-Assistant-Integration, die Heizkörperventile nach einem externen Raumsensor regelt statt nach dem Sensor am Heizkörper.

Pro Raum: ein Ventil (`climate`), ein Raumsensor (`sensor`) und eine Wunschtemperatur als eigene Thermostat-Entität. Optional kommen Fenster-offen-Erkennung, ein Zeitplan und eine Anwesenheitsabsenkung dazu.

## Funktionsweise

* Jeder Raum wird als eigene `climate`-Entität angelegt, zum Beispiel `climate.thermik_arbeitszimmer`.
* Die Wunschtemperatur stellst du an dieser Entität ein, in 0,5-Grad-Schritten und ohne Funkverzögerung.
* Bei jeder Änderung von Wunschtemperatur, Raumsensor oder einer der optionalen Quellen, und zusätzlich jede Minute, wird das Ventil gesteuert:
   * Raum kälter als Soll minus 0,5 Grad: Ventil auf 30 °C (voll auf)
   * Raum so warm wie der Soll oder wärmer: Ventil auf 5 °C (zu)
   * dazwischen: Ventil bleibt, wie es ist (Hysterese)
* Ist das Ventil nicht erreichbar, wird nichts gesendet.

## Optionale Funktionen

Alle drei Funktionen sind pro Raum einstellbar und können leer bleiben. Dann verhält sich Thermik wie bisher.

### Fenster offen

* Ein oder mehrere Fenster-/Türkontakte (`binary_sensor`) auswählen.
* Ist einer davon durchgehend länger als die eingestellte Zeit offen (Standard 2 Minuten, maximal 60), geht das Ventil zu.
* Kurzes Lüften bleibt dadurch ohne Wirkung.
* Sind alle Fenster wieder zu, regelt Thermik sofort wieder normal.

### Zeitplan

* Einen Schedule-Helfer (`schedule`) auswählen.
* Ist der Zeitplan an, gilt deine Wunschtemperatur.
* Ist der Zeitplan aus, gilt die Absenk-Temperatur (Standard 18 °C), sofern sie niedriger ist als die Wunschtemperatur.

### Anwesenheit

* Eine oder mehrere Personen (`person`) oder Tracker (`device_tracker`) auswählen.
* Ist niemand davon zu Hause, und das länger als die eingestellte Zeit (Standard 30 Minuten), gilt die Abwesenheits-Temperatur (Standard 17 °C), sofern sie niedriger ist als der aktuelle Soll.
* Sind alle Personen unbekannt oder nicht verfügbar, wird normal geheizt.

Gelten Zeitplan und Abwesenheit gleichzeitig, zählt der niedrigere Wert.

### Zusätzliche Attribute

Die Thermostat-Entität zeigt, was gerade gilt:

* `effective_target`: die Temperatur, nach der gerade geregelt wird
* `window_open`: Fenster-Absenkung ist aktiv (nur mit Fensterkontakten)
* `schedule_eco`: Zeitplan steht auf Absenkung (nur mit Zeitplan)
* `away`: Abwesenheitsabsenkung ist aktiv (nur mit Anwesenheit)

## Installation

Ab Home Assistant 2026.11 (Marketplace):

1. Einstellungen, Marketplace öffnen.
2. Menü oben rechts, "Add from link".
3. `https://github.com/b1ackbyte/thermik` eintragen, Kategorie Integration.
4. Thermik installieren und Home Assistant neu starten.
5. Einstellungen, Geräte & Dienste, Integration hinzufügen, Thermik.
6. Pro Raum Name, Ventil und Raumsensor auswählen. Fenster, Zeitplan und Anwesenheit sind optional und lassen sich später unter "Konfigurieren" ergänzen.

Mit älteren Versionen funktioniert dasselbe über HACS: Menü, Benutzerdefinierte Repositories, Repo-Adresse eintragen, Kategorie Integration.

## Hinweise

* Das Ventil wird nur auf 5 °C oder 30 °C gestellt, nie dazwischen.
* Läuft parallel eine Automation, die dasselbe Ventil steuert, diese ausschalten.
* Den Schedule-Helfer für den Zeitplan legst du vorher in Home Assistant an (Einstellungen, Geräte & Dienste, Helfer).
* Die Integration ist neu und wenig getestet. Erst mit einem Raum probieren.

## Unterstützen

Dir gefällt Thermik? Dann freue ich mich über einen Kaffee. Das hält mich wach für den nächsten Code. Danke dir!

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-b1ackbyte-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/b1ackbyte)
