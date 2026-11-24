# thermik

Thermik - Home Assistant Integration
Regelt Heizkörperventile nach einem externen Raumsensor statt nach dem Sensor am Heizkörper. Pro Raum: ein Ventil (climate), ein Raumsensor (sensor) und eine Wunschtemperatur als eigene Thermostat-Entität.
Funktionsweise
• Jeder Raum wird als eigene climate-Entität angelegt, zum Beispiel climate.thermik_arbeitszimmer.
• Die Wunschtemperatur stellst du an dieser Entität ein, in 0,5-Grad-Schritten, ohne Funkverzögerung.
• Bei jeder Änderung von Wunschtemperatur oder Raumsensor und zusätzlich jede Minute wird das Ventil gesteuert:
    ◦ Raum kälter als Wunsch minus 0,5 Grad: Ventil auf 30 °C (voll auf)
    ◦ Raum so warm wie der Wunsch oder wärmer: Ventil auf 5 °C (zu)
    ◦ dazwischen: Ventil bleibt, wie es ist (Hysterese)
• Ist das Ventil nicht erreichbar, wird nichts gesendet.
