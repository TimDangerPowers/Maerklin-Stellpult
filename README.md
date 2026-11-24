# Märklin-Stellpult (Fensterbahn)

Firmware, Pult-Druckteile und Verkabelung für die Fensterbank-Anlage.

- `fensterbahn/` – Arduino-Sketch für den ESP32 WROOM-32 (Board „ESP32 Dev Module“, Partition „Minimal SPIFFS“).
  Bibliotheken: Adafruit NeoPixel, Adafruit MCP23017 Arduino Library, U8g2.
- `firmware/` – fertige Firmware, baut GitHub automatisch bei jeder Änderung an `fensterbahn/`.
- `werkzeuge/gen_web.py` – erzeugt `fensterbahn/web.h` (Website im ESP) aus `pult/stellpult_v7.py`.
- `pult/` – 3D-Modell des Stellpults (CadQuery).
- `elektronik/` – Elektronik-Box, Schaltplan, Steckplan (`verkabelung.pdf`).

## Updates
1. Neue Version: `FW_VERSION` in `fensterbahn/fensterbahn.ino` hochzählen und auf `main` pushen.
2. GitHub baut `firmware/fensterbahn.bin` und `firmware/version.txt`.
3. Der ESP schaut beim Einschalten (und per „Jetzt nach Update suchen“ auf der Website) nach und lädt neuere Versionen.

Das Repo ist privat: Auf der Website des ESP unter Einstellungen einen GitHub-Schlüssel (Fine-grained Token,
nur dieses Repo, „Contents: Read-only“) eintragen. Er wird nur im ESP gespeichert, nie im Code.
WLAN-Daten ebenfalls nur auf der Website eintragen. `secrets.h` wird nie hochgeladen.
