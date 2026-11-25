# Thermik

Home-Assistant-Integration, die Heizkörperventile nach einem **externen Raumsensor** regelt statt nach dem Sensor am Heizkörper.

Pro Raum: ein Ventil (`climate`), ein Raumsensor (`sensor`) und eine Wunschtemperatur als eigene Thermostat-Entität.

## Funktionsweise

- Jeder Raum wird als eigene `climate`-Entität angelegt, zum Beispiel `climate.thermik_arbeitszimmer`.
- Die Wunschtemperatur stellst du an dieser Entität ein, in 0,5-Grad-Schritten und ohne Funkverzögerung.
- Bei jeder Änderung von Wunschtemperatur oder Raumsensor, und zusätzlich jede Minute, wird das Ventil gesteuert:
  - Raum kälter als Wunsch minus 0,5 Grad: Ventil auf 30 °C (voll auf)
  - Raum so warm wie der Wunsch oder wärmer: Ventil auf 5 °C (zu)
  - dazwischen: Ventil bleibt, wie es ist (Hysterese)
- Ist das Ventil nicht erreichbar, wird nichts gesendet.

## Installation über Marketplace

1. Marketplace öffnen, Menü oben rechts, **Benutzerdefinierte Repositories**.
2. `https://github.com/b1ackbyte/thermik` eintragen, Kategorie **Integration**.
3. Thermik installieren und Home Assistant neu starten.
4. **Einstellungen, Geräte & Dienste, Integration hinzufügen, Thermik.**
5. Pro Raum Name, Ventil und Raumsensor auswählen.

## Hinweise

- Das Ventil wird nur auf 5 °C oder 30 °C gestellt, nie dazwischen.
- Läuft parallel eine Automation, die dasselbe Ventil steuert, diese ausschalten.
- Die Integration ist neu und wenig getestet. Erst mit einem Raum probieren.
