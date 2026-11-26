<p align="center">
<img src="thermik.png" alt="Thermik" width="400">
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


----------------------------------------------------------------------------------------------------------------------------------


# Thermik

Home Assistant integration that controls radiator valves based on an external room sensor instead of the sensor on the radiator itself.

Per room: one valve (`climate`), one room sensor (`sensor`) and a target temperature as its own thermostat entity. Optionally add window detection, a schedule and presence-based setback.

## How it works

* Each room is created as its own `climate` entity, for example `climate.thermik_arbeitszimmer`.
* You set the target temperature on this entity, in 0.5-degree steps and without radio delay.
* On every change of the target temperature, the room sensor or one of the optional sources, and additionally every minute, the valve is controlled:
   * Room colder than target minus 0.5 degrees: valve set to 30 °C (fully open)
   * Room at or above the target: valve set to 5 °C (closed)
   * In between: the valve stays as it is (hysteresis)
* If the valve is unavailable, nothing is sent.

## Optional features

All three features can be set per room and can be left empty. Without them, Thermik behaves as before.

### Window open

* Select one or more window/door contacts (`binary_sensor`).
* If any of them stays open longer than the configured time (default 2 minutes, maximum 60), the valve is closed.
* This means short airing has no effect.
* As soon as all windows are closed again, Thermik resumes normal control immediately.

### Schedule

* Select a schedule helper (`schedule`).
* While the schedule is on, your target temperature applies.
* While the schedule is off, the setback temperature applies (default 18 °C), as long as it is lower than the target temperature.

### Presence

* Select one or more persons (`person`) or trackers (`device_tracker`).
* If nobody is home, and this lasts longer than the configured time (default 30 minutes), the away temperature applies (default 17 °C), as long as it is lower than the current target.
* If all persons are unknown or unavailable, heating continues normally.

If schedule and away apply at the same time, the lower value wins.

### Additional attributes

The thermostat entity shows what currently applies:

* `effective_target`: the temperature currently being controlled to
* `window_open`: window setback is active (only with window contacts)
* `schedule_eco`: schedule is in setback (only with a schedule)
* `away`: away setback is active (only with presence)

## Installation

From Home Assistant 2026.11 (Marketplace):

1. Open Settings, Marketplace.
2. Top right menu, "Add from link".
3. Enter `https://github.com/b1ackbyte/thermik`, category Integration.
4. Install Thermik and restart Home Assistant.
5. Settings, Devices & services, Add integration, Thermik.
6. For each room, select a name, valve and room sensor. Window, schedule and presence are optional and can be added later under "Configure".

With older versions, the same works through HACS: menu, Custom repositories, enter the repository address, category Integration.

## Notes

* The valve is only ever set to 5 °C or 30 °C, never in between.
* If an automation is also controlling the same valve, turn it off.
* Create the schedule helper for the schedule feature in Home Assistant beforehand (Settings, Devices & services, Helpers).
* The integration is new and not heavily tested. Try it with one room first.

## Support

Do you like Thermik? Then I would be happy about a [coffee](https://buymeacoffee.com/b1ackbyte). It keeps me awake for the next piece of code. Thank you!


[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-b1ackbyte-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/b1ackbyte)
