# Elektronik Märklin-Fensterbahn (Stand 21.11.2026, v2: 16er + 8er Relais, Display)

- `schaltplan.pdf`: 3 Seiten (Strom und Steuerung, Märklin-Seite, Belegung zum Abhaken)
- `steckplan.pdf`: 4 Seiten mit Bildern, an jedem Pin steht, wohin das Kabel geht (ESP32, Pegelwandler/8er-Relais/Display, Relais-MCP → 16er-Relais, Pult-MCP → Taster)
- `elektronik-druck.zip`: Box unter der Bergecke (P4 links). Enthält `box-haube` (mit der geschlossenen Seite aufs Bett), `box-montageplatte` (flach, v3 mit festen Löchern), `abstandshuelse-6mm` (8× drucken), `klemmleiste-mcp` (1×) und `klemmleiste-llc` (2×). Dazu `lochbild-schablone.pdf` (1:1 auf Papier, zum Prüfen vor dem Druck).
- `stellpult-v7-druck.zip`: Stellpult v7 (Display mit 4 Schrauben, Knöpfe 10/13 mm, Brücke als Überführung, Gehäuse 55 mm hoch) + Bauanleitung

## BerryBase-Bestellung (Lager am 21.11. auf der Produktseite geprüft)
| Teil | Stück | Preis | Link |
|---|---|---|---|
| 16-Kanal-Relais RELM-16 | 1 | 12,10 € | https://www.berrybase.de/5v-16-kanal-relais-modul |
| 8-Kanal-Relais HLRELM-8 (High/Low wählbar) | 1 | 8,40 € | https://www.berrybase.de/5v-8-kanal-relais-modul-mit-definierbarem-schaltsignal-high-low |
| MCP23017 Soldered (Relais-Steuerung) | 1 | 4,75 € | https://www.berrybase.de/soldered-mcp23017-i2c-io-expander-qwiic-16-digitale-ein-ausgaenge-8-adressen-2x-qwiic |
| Pegelwandler LLC | 2 | je 0,90 € | im Shop nach „Logic Level Converter“ suchen |
| OLED 1,3" SH1106 blau (Stifte eingelötet) | 1 | 6,70 € | https://www.berrybase.de/1.3-128x64-oled-display-sh1106-iic-i2c-interface-einfarbig-blau |
| Netzteil LRS-50-5, WAGOs, Schrauben | | | falls noch nicht bestellt, aus der alten Bestellliste |

Das Waveshare-MCP ist nicht mehr lieferbar, deshalb nehmen wir das Soldered-Board plus einen zweiten LLC.

## Box einbauen
1. Die Haube (205 × 237 × 51 mm) mit der geschlossenen Seite unter die Ecke von P4 schrauben, die links zum Berg hin übersteht. Sie sitzt zwischen den Latten, bei Bedarf gedreht. Dafür 4 × Spanplattenschraube 4 × 30 von innen.
2. Module auf die Montageplatte (alles ohne Clips, nur Schrauben):
   - **ESP-Shield:** über `shield-adapter` (100 % Füllung): Adapter mit 4 × 3×12 von unten in die 4 Shield-Löcher der Platte, Shield mit 4 × 3×10 auf die 4 Säulen (USB links). Vorher mit `shield-schablone.pdf` prüfen.
   - **16er-Relais:** 4× M3×16 von unten durch die Platte (Kopf versenkt), Abstandshülse 6 mm drauf, Platine drauf, M3-Mutter oben. Die Löcher haben ±0,8 mm Spiel.
   - **MCP und 2× LLC:** Platine in die Mulde legen (Pins nach oben), Klemmleiste drüber und mit 2 × Schraube 3×10 in die kleinen Dome schrauben. Die Leiste drückt zwischen den Pinreihen.
   - **8er-Relais:** kommt auf eine Adapterplatte (folgt, wenn das Board da ist), die mit 4 × 3×12 in die 4 Dome geschraubt wird.
   - Einkauf Schrauben: 8 × M3×16 + 8 × Mutter M3, 6 × 3×10 und 4 × 3×12 (Blech- oder Spanplattenschrauben).
3. Beim 8er-Relais **alle Jumper auf HIGH** stecken.
4. Nach Schaltplan verkabeln und die Kabel durch die Kerben am Rand führen.
5. Die Platte von unten an die Haube schrauben: 4 × 3 × 12 in die Eck-Dome.

Druck: PLA, 3 Wände, 15 % Füllung, ohne Stützen. Die Haube passt auf die K2.

## Was du schon bauen kannst, solange die Teile unterwegs sind
Unterbau, Gleise, Stützen, Box-Haube und Montageplatte, Pult-Gehäuse und Tasterbrücken. Den Pult-Deckel und die Trägerplatte erst drucken, wenn das Display da ist und gemessen wurde (ca. 35,5 × 33,8 mm).

**Firmware:** Die Relais laufen über den zweiten MCP23017. Mühle und Qualm liegen auf GPIO 32/33 (8er IN1/2), IN3–8 sind Reserve (GPIO 4, 13, 16–19). Dazu kommen der Taster ANIMATION und das Display mit Statusmeldungen. Das Firmware-Update kommt, bevor verkabelt wird.
