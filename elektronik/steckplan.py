"""Bebilderter Steckplan: jedes Modul mit seinen Pins, an jedem benutzten Pin ein Schild, wohin das Kabel geht.
Ausgabe: steckplan.pdf + steckplan-1..4.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

FARBE = {"5V": "#d62728", "3V3": "#ff7f0e", "GND": "#222222", "SDA": "#1f5fbf", "SCL": "#17becf",
         "DAT": "#2ca02c", "SIG": "#9467bd", "IN": "#8c564b", "TAST": "#e377c2"}
NAMEN = {"5V": "5 V", "3V3": "3,3 V", "GND": "GND / Masse", "SDA": "I²C SDA", "SCL": "I²C SCL",
         "DAT": "LED-Daten", "SIG": "Steuerleitung", "IN": "Relais-Eingang", "TAST": "Taster / Kontakt"}

def neue_seite(titel, unter):
    fig = plt.figure(figsize=(16.54, 11.69))
    ax = fig.add_axes([0.01, 0.07, 0.98, 0.86]); ax.set_xlim(0, 420); ax.set_ylim(0, 260); ax.axis("off"); ax.set_aspect("equal")
    fig.text(.03, .955, titel, fontsize=18, weight="bold")
    fig.text(.03, .93, unter, fontsize=10, color="#555")
    x = .03
    for k in ("5V", "3V3", "GND", "SDA", "SCL", "DAT", "SIG", "IN", "TAST"):
        fig.patches.append(Rectangle((x, .03), .025, .008, transform=fig.transFigure, color=FARBE[k], figure=fig))
        fig.text(x + .03, .034, NAMEN[k], fontsize=9, va="center"); x += .105
    return fig, ax

def platine(ax, x, y, w, h, name, unter="", fc="#1d5e9e", tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=3", fc=fc, ec="#111", lw=1.5))
    ax.text(x + w/2, y + h/2 + (3 if unter else 0), name, ha="center", va="center", fontsize=12, weight="bold", color=tc)
    if unter: ax.text(x + w/2, y + h/2 - 5, unter, ha="center", va="center", fontsize=8.5, color=tc)

def pin(ax, x, y, label, seite, benutzt=True, lab_innen=True):
    ax.add_patch(Rectangle((x - 1.6, y - 1.6), 3.2, 3.2, fc="#f2c200" if benutzt else "#888", ec="#222", lw=.6, zorder=5))
    ax.add_patch(Circle((x, y), .7, fc="#333", zorder=6))
    if lab_innen:
        dx = {"l": 3, "r": -3, "o": 0, "u": 0}[seite]; dy = {"l": 0, "r": 0, "o": -3.2, "u": 3.2}[seite]
        ha = {"l": "left", "r": "right", "o": "center", "u": "center"}[seite]
        va = {"l": "center", "r": "center", "o": "top", "u": "bottom"}[seite]
        rot = 90 if seite in "ou" else 0
        ax.text(x + dx, y + dy, label, ha=ha, va=va, fontsize=7.5, color="white", weight="bold", rotation=rot, zorder=7)

def schild(ax, x, y, seite, text, netz, laenge=14, breite=None):
    """Kabel vom Pin nach außen + Schild mit Ziel."""
    c = FARBE[netz]
    if seite == "l": x2, y2 = x - laenge, y
    elif seite == "r": x2, y2 = x + laenge, y
    elif seite == "o": x2, y2 = x, y + laenge
    else: x2, y2 = x, y - laenge
    ax.plot([x, x2], [y, y2], color=c, lw=2.6, solid_capstyle="round", zorder=4)
    ha = {"l": "right", "r": "left", "o": "center", "u": "center"}[seite]
    va = {"l": "center", "r": "center", "o": "bottom", "u": "top"}[seite]
    rot = 90 if seite in "ou" else 0
    ax.text(x2 + {"l": -1, "r": 1, "o": 0, "u": 0}[seite], y2 + {"o": 1, "u": -1}.get(seite, 0), text, ha=ha, va=va,
            fontsize=8.3, rotation=rot, zorder=8,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=c, lw=1.6))

def hinweis(ax, x, y, text, w=None, fc="#fff6d6"):
    ax.text(x, y, text, fontsize=9, va="top", ha="left", wrap=True,
            bbox=dict(boxstyle="round,pad=0.6", fc=fc, ec="#c9a227"))

pdf = PdfPages("steckplan.pdf")

# =============== Seite 1: ESP32 ===============
fig, ax = neue_seite("Steckplan 1/5 – ESP32 auf dem Shield",
    "Draufsicht, USB-Buchse unten. Auf dem Shield hat jeder Pin drei Stifte: S = Signal, V = Spannung, G = Masse. Steck die Signalkabel immer auf S.")
X0, W, Y0, P = 175, 70, 30, 10.5
LINKS = ["3V3", "EN", "VP 36", "VN 39", "34", "35", "32", "33", "25", "26", "27", "14", "12", "GND", "13", "D2", "D3", "CMD", "5V"]
RECHTS = ["GND", "23", "22", "TX", "RX", "21", "GND", "19", "18", "5", "17", "16", "4", "0", "2", "15", "D1", "D0", "CLK"]
H = P * (len(LINKS) - 1) + 24
platine(ax, X0, Y0 - 12, W, H, "ESP32\nWROOM-32", "38 Pins", fc="#2b2b2b")
ax.add_patch(Rectangle((X0 + 15, Y0 + H - 22), 40, 9, fc="#bbb", ec="#555")); ax.text(X0 + 35, Y0 + H - 17.5, "Antenne", ha="center", va="center", fontsize=8)
ax.add_patch(Rectangle((X0 + 26, Y0 - 16), 18, 8, fc="#ccc", ec="#555")); ax.text(X0 + 35, Y0 - 12, "USB", ha="center", va="center", fontsize=8)
ZIEL_L = {
    "3V3": ("3,3 V → LLC1 LV, LLC2 LV, Kabel Ader 3", "3V3"),
    
    "14": ("→ LLC1 LV1 (Pult-LEDs)", "DAT"), 
    "GND": ("→ WAGO GND", "GND"), "5V": ("← WAGO 5 V", "5V"),
}
ZIEL_R = {
    "GND": ("→ WAGO GND", "GND"), "22": ("SCL → Kabel Ader 5 + LLC2 LV2", "SCL"),
    "21": ("SDA → Kabel Ader 4 + LLC2 LV1", "SDA"),
    
    
    
    "2": ("→ LLC1 LV2 (Häuser)", "DAT"), 
}
gnd_l = gnd_r = 0
for i, n in enumerate(LINKS):
    y = Y0 + H - 24 - i * P
    z = ZIEL_L.get(n)
    if n == "GND":
        gnd_l += 1; z = ZIEL_L["GND"] if gnd_l == 1 else None
    pin(ax, X0 + 4, y, n, "l", benutzt=z is not None)
    if z: schild(ax, X0 + 4, y, "l", z[0], z[1], laenge=12)
for i, n in enumerate(RECHTS):
    y = Y0 + H - 24 - i * P
    z = ZIEL_R.get(n)
    if n == "GND":
        gnd_r += 1; z = ZIEL_R["GND"] if gnd_r == 1 else None
    pin(ax, X0 + W - 4, y, n, "r", benutzt=z is not None)
    if z: schild(ax, X0 + W - 4, y, "r", z[0], z[1], laenge=12)
hinweis(ax, 318, 70, "Gelb = belegt, grau = frei lassen.\n\nAchtung: GPIO 0, 2, 5, 12 und 15 sind\n„Start-Pins“. Nur die hier gezeigten\nbenutzen, sonst startet der ESP evtl. nicht.\n\nDie Pin-Reihenfolge gilt für das übliche\n38-Pin-Board. Steht auf deinem Shield\neine andere Reihenfolge: nach dem\nAufdruck (z. B. „G21“) gehen, nicht\nnach der Position.")
hinweis(ax, 8, 70, "Strom fürs Shield:\n5 V und GND vom WAGO an den\n5-V-Eingang des Shields\n(Schraubklemme oder 5V/GND-Pin).\n\nZum Flashen per USB vorher\ndas Netzteil ausschalten.", fc="#fde2e2")
pdf.savefig(fig); fig.savefig("steckplan-1.png", dpi=100); plt.close(fig)

# =============== Seite 2: LLC1, LLC2, 8er-Relais, Display ===============
fig, ax = neue_seite("Steckplan 2/5 – Pegelwandler und Display",
    "Die Pegelwandler machen aus 3,3 V (ESP-Seite = LV) die 5 V (HV), die LED-Ketten und der Relais-MCP brauchen.")
def llc(x0, y0, name, ziele_lv, ziele_hv):
    w, h = 44, 62
    platine(ax, x0, y0, w, h, name, fc="#1a7f3c"); ax.text(x0 + w/2, y0 - 4, "links LV = 3,3 V  |  rechts HV = 5 V", ha="center", va="top", fontsize=8.5, color="#1a7f3c", weight="bold")
    lv = ["LV1", "LV2", "LV", "GND", "LV3", "LV4"]; hv = ["HV1", "HV2", "HV", "GND", "HV3", "HV4"]
    for i, n in enumerate(lv):
        y = y0 + h - 8 - i * 9.5; z = ziele_lv.get(n)
        pin(ax, x0 + 4, y, n, "l", z is not None)
        if z: schild(ax, x0 + 4, y, "l", z[0], z[1], laenge=10)
    for i, n in enumerate(hv):
        y = y0 + h - 8 - i * 9.5; z = ziele_hv.get(n)
        pin(ax, x0 + w - 4, y, n, "r", z is not None)
        if z: schild(ax, x0 + w - 4, y, "r", z[0], z[1], laenge=10)
llc(78, 170, "LLC 1", {"LV1": ("← ESP GPIO 14", "DAT"), "LV2": ("← ESP GPIO 2", "DAT"), "LV": ("← ESP 3V3", "3V3"), "GND": ("← GND", "GND")},
    {"HV1": ("→ Kabel Ader 6 (Pult-LEDs)", "DAT"), "HV2": ("→ Häuser: DIN von Haus 1", "DAT"), "HV": ("← WAGO 5 V", "5V"), "GND": ("← GND", "GND")})
llc(78, 75, "LLC 2", {"LV1": ("← ESP GPIO 21 (SDA)", "SDA"), "LV2": ("← ESP GPIO 22 (SCL)", "SCL"), "LV": ("← ESP 3V3", "3V3"), "GND": ("← GND", "GND")},
    {"HV1": ("→ Relais-MCP SDA", "SDA"), "HV2": ("→ Relais-MCP SCL", "SCL"), "HV": ("← WAGO 5 V", "5V"), "GND": ("← GND", "GND")})
# OLED
x0, y0, w, h = 320, 12, 50, 48
platine(ax, x0, y0, w, h, "OLED 1,3\"", "im Pult, Vorderseite", fc="#1d5e9e")
ax.add_patch(Rectangle((x0 + 4, y0 + 6), w - 8, 26, fc="#101030", ec="#000"))
for i, (n, z) in enumerate([("VCC", ("← 3,3 V (Ader 3)", "3V3")), ("GND", ("← GND (Ader 2)", "GND")), ("SCL", ("← SCL (Ader 5)", "SCL")), ("SDA", ("← SDA (Ader 4)", "SDA"))]):
    xx = x0 + 13 + i * 8
    pin(ax, xx, y0 + h - 5, n, "o", True)
    schild(ax, xx, y0 + h - 5, "o", z[0], z[1], laenge=8)
hinweis(ax, 215, 50, "Display am besten an den\nPult-MCP mit dranhängen:\ngleiche 4 Leitungen\n(3,3 V, GND, SDA, SCL).", fc="#e3eefc")
pdf.savefig(fig); fig.savefig("steckplan-2.png", dpi=100); plt.close(fig)

# =============== Seite 3: Relais-MCP -> RELM-16 ===============
fig, ax = neue_seite("Steckplan 3/5 – Relais-MCP (Soldered MCP23017) → 16er-Relais RELM-16",
    "16 Leitungen, jede genau eins zu eins: GPA0 → IN1 … GPB7 → IN16. Am besten ein 16-adriges Flachband oder 16 Dupont-Kabel in Regenbogenfarben.")
mx, my, mw, mh = 40, 40, 70, 190
platine(ax, mx, my, mw, mh, "MCP23017\n(Relais)", "Soldered, 5 V", fc="#7a1d6e")
rx, ry, rw, rh = 250, 20, 135, 230
platine(ax, rx, ry, rw, rh, "", fc="#1d4f91")
ax.text(rx + 120, ry + rh/2 + 40, "RELM-16\n16 Relais\n\n(schaltet\nbei LOW)", ha="center", va="center", fontsize=12, weight="bold", color="white")
for k in range(16):
    ax.add_patch(Rectangle((rx + 75, ry + rh - 18 - k*13.2), 30, 10, fc="#2a6fd6", ec="#123"))
    ax.text(rx + 90, ry + rh - 13 - k*13.2, f"K{k+1}", ha="center", va="center", color="white", fontsize=7)
BEDEUTUNG = ["Puls", "W1 gerade", "W1 abzweig", "W2 gerade", "W2 abzweig", "W3 gerade", "W3 abzweig", "W4 gerade",
             "W4 abzweig", "S1 rot", "S1 grün", "S2 rot", "S2 grün", "Entkuppler", "Mühle", "Qualm"]
bunt = plt.cm.tab20.colors
for k in range(16):
    y = my + mh - 30 - k * 9.6
    ry_k = ry + rh - 13 - k * 13.2
    n = f"GPA{k}" if k < 8 else f"GPB{k-8}"
    pin(ax, mx + mw - 4, y, n, "r", True)
    pin(ax, rx + 4, ry_k, f"IN{k+1}", "l", True)
    xm = 140 + k * 5.5
    ax.plot([mx + mw - 4, xm, xm, rx + 4], [y, y, ry_k, ry_k], color=bunt[k], lw=2.2, zorder=3)
    ax.text(rx + 24, ry_k, BEDEUTUNG[k], fontsize=7.5, color="white", va="center")
for i, (n, z) in enumerate([("VCC", ("← WAGO 5 V", "5V")), ("GND", ("← GND", "GND")), ("SDA", ("← LLC2 HV1", "SDA")), ("SCL", ("← LLC2 HV2", "SCL"))]):
    y = my + mh - 30 - i * 12
    pin(ax, mx + 4, y, n, "l", True); schild(ax, mx + 4, y, "l", z[0], z[1], laenge=8)
for i, (n, z) in enumerate([("VCC", ("← 5 V", "5V")), ("JD-VCC", ("← 5 V", "5V")), ("GND", ("← GND", "GND"))]):
    yy = ry + 40 - i * 12
    pin(ax, rx + rw - 4, yy, n, "r", True); schild(ax, rx + rw - 4, yy, "r", z[0], z[1], laenge=6)
ax.text(rx + rw + 2, ry + 50, "Jumper VCC–JD-VCC\ndrauf lassen", fontsize=7.5, color="#555")
hinweis(ax, 4, 30, "Adresse: A0–A2 so lassen, wie\nes geliefert wird. Nur der Pult-MCP\nmuss auf 0x20 (A0–A2 an GND)\nstehen. Die Firmware findet den\nRelais-MCP selbst.\n\nDie Reihenfolge der Pins kann auf\ndeinen Platinen anders sein:\nimmer nach dem Aufdruck stecken.")
pdf.savefig(fig); fig.savefig("steckplan-3.png", dpi=100); plt.close(fig)

# =============== Seite 4: Pult-MCP ===============
fig, ax = neue_seite("Steckplan 4/5 – Im Pult: MCP23017 (Funduino) → Taster",
    "Jeder Taster KY-004 hat 3 Stifte: S = Signal → an den MCP-Pin, „–“ = Masse → GND, der mittlere Stift bleibt frei.")
mx, my, mw, mh = 170, 50, 80, 180
platine(ax, mx, my, mw, mh, "MCP23017\n(Pult)", "3,3 V, Adresse 0x20", fc="#7a1d6e")
A = ["W1", "W2", "W3", "W4", "S1 grün", "S1 rot", "S2 grün", "S2 rot"]
B = ["E (Entkuppler)", "T1", "T2", "AUTO", "STOP", "LICHT", "ANIMATION", None]
for k in range(8):
    y = my + mh - 25 - k * 18
    pin(ax, mx + 4, y, f"GPA{k}", "l", True); schild(ax, mx + 4, y, "l", f"← Taster {A[k]} (S)", "TAST", laenge=14)
    pin(ax, mx + mw - 4, y, f"GPB{k}", "r", B[k] is not None)
    if B[k]: schild(ax, mx + mw - 4, y, "r", f"← Taster {B[k]} (S)", "TAST", laenge=14)
for i, (n, z) in enumerate([("VCC", ("← 3,3 V (Ader 3)", "3V3")), ("GND", ("← GND (Ader 2)", "GND")), ("SDA", ("← SDA (Ader 4)", "SDA")),
                            ("SCL", ("← SCL (Ader 5)", "SCL")), ("A0 A1 A2", ("→ GND", "GND")), ("RESET", ("→ 3,3 V", "3V3"))]):
    xx = mx + 8 + i * 13
    pin(ax, xx, my + 4, n, "u", True); schild(ax, xx, my + 4, "u", z[0], z[1], laenge=8)
hinweis(ax, 320, 70, "Alle „–“-Stifte der 16 Taster\nan eine gemeinsame GND-Leitung\n(WAGO im Pult oder Lüsterleiste).\n\nPult-LEDs (Lichterkette):\n5 V ← Ader 1, GND ← Ader 2,\nDaten ← Ader 6.\n(25 Perlen, Pfeil zeigt vom\nESP weg)", fc="#e3eefc")
pdf.savefig(fig); fig.savefig("steckplan-4.png", dpi=100); plt.close(fig)

# =============== Seite 5: Häuser-LEDs, Pult-Lichterkette, Taster KY-004 ===============
fig, ax = neue_seite("Steckplan 5/5 – Häuser-LEDs, Pult-Lichterkette und Taster",
    "Die LED-Daten laufen immer in eine Richtung: DIN (Eingang) → DOUT (Ausgang) → nächstes DIN. Strom (5 V / GND) darf man überall dazugeben.")
# WS2812-Stäbe (Häuser)
for i in range(3):
    x0, y0, w, h = 40 + i * 95, 175, 70, 22
    platine(ax, x0, y0, w, h, "", fc="#2b2b2b")
    ax.text(x0 + w/2, y0 + h + 3, f"Haus {i+1}  (WS2812, 8 LEDs)", ha="center", fontsize=10, weight="bold")
    for k in range(8):
        ax.add_patch(Rectangle((x0 + 19 + k * 4.2, y0 + 9), 3.2, 3.2, fc="#f5f5f5", ec="#777", zorder=5))
    for j, n in enumerate(["DIN", "5V", "GND"]):
        yy = y0 + h - 5 - j * 6.5
        pin(ax, x0 + 3, yy, n, "l", True)
    for j, n in enumerate(["DOUT", "5V", "GND"]):
        yy = y0 + h - 5 - j * 6.5
        pin(ax, x0 + w - 3, yy, n, "r", True)
    if i == 0:
        schild(ax, x0 + 3, y0 + h - 5, "l", "← LLC1 HV2", "DAT", laenge=6)
    else:
        xa = x0 - 95 + 70 - 3; xb = x0 + 3
        for j, net in enumerate(["DAT", "5V", "GND"]):
            yy = y0 + h - 5 - j * 6.5
            ax.plot([xa, xb], [yy, yy], color=FARBE[net], lw=2.6, zorder=4)
schild(ax, 40 + 3, 175 + 22 - 5 - 6.5, "l", "5 V + GND ← WAGO", "5V", laenge=6)
ax.text(330, 186, "… weiter bis Haus 6", fontsize=10, va="center")
hinweis(ax, 40, 160, "Löten: DOUT → DIN, 5V → 5V, GND → GND zum nächsten Haus (3 kurze Litzen, Pads vorher verzinnen).\n"
        "Bei mehr als 3 Häusern 5 V und GND am letzten Haus nochmal vom WAGO dazugeben (gleichmäßige Helligkeit).\n"
        "Reihenfolge laut Firmware: 1 Bahnhof, 2 Wohnhaus, 3 Wohnhaus, 4 Fabrik, 5 Mühle, 6 Wohnhaus.", fc="#e8f6e8")
# Lichterkette im Pult
x0, y0 = 60, 75
platine(ax, x0, y0, 60, 30, "Lichterkette", "Pult, 25 Perlen", fc="#1a7f3c")
for j, (n, z) in enumerate([("5V", ("← Ader 1 (5 V)", "5V")), ("GND", ("← Ader 2 (GND)", "GND")), ("DIN", ("← Ader 6 (LED-Daten)", "DAT"))]):
    yy = y0 + 25 - j * 9
    pin(ax, x0 + 3, yy, n, "l", True); schild(ax, x0 + 3, yy, "l", z[0], z[1], laenge=4)
for k in range(5):
    ax.add_patch(Circle((x0 + 90 + k * 14, y0 + 15), 3, fc="#ffe9a8", ec="#a87b00"))
    if k: ax.plot([x0 + 90 + (k-1) * 14 + 3, x0 + 90 + k * 14 - 3], [y0 + 15]*2, color="#555", lw=1.5)
ax.plot([x0 + 60, x0 + 87], [y0 + 15]*2, color="#555", lw=1.5)
ax.annotate("", xy=(x0 + 160, y0 + 8), xytext=(x0 + 90, y0 + 8), arrowprops=dict(arrowstyle="->", lw=1.5))
ax.text(x0 + 125, y0 + 4, "Datenrichtung (Pfeil auf der Kette)", ha="center", va="top", fontsize=8.5)
hinweis(ax, 60, 62, "Den Anfang der Kette (Stecker-/Kabelende, an dem DIN bzw. der Pfeil wegzeigt) an Ader 6.\n"
        "Perle 1 = AUTO, 2 = LICHT, 3 = ANIMATION, Perle 4 bleibt frei, dann W1 grün, W1 abzweig, S2, S1, W2 …\n"
        "Reihenfolge der Halter steht auf der Montageseite (pult-aufbau-erklaert.png).", fc="#e8f6e8")
# KY-004
x0, y0, w, h = 330, 75, 50, 66
platine(ax, x0, y0, w, h, "", fc="#1d5e9e")
ax.add_patch(Rectangle((x0 + 14, y0 + 30), 22, 22, fc="#222", ec="#000")); ax.add_patch(Circle((x0 + 25, y0 + 41), 6, fc="#444", ec="#000"))
ax.text(x0 + w/2, y0 + 60, "KY-004 (von oben)", ha="center", color="white", fontsize=9, weight="bold")
for j, (n, z) in enumerate([("S", ("→ Pult-MCP (S. 4)", "TAST")), ("+", None), ("–", ("→ GND im Pult", "GND"))]):
    xx = x0 + 15 + j * 10
    pin(ax, xx, y0 + 6, n, "u", z is not None)
    if z: schild(ax, xx, y0 + 6, "u", z[0], z[1], laenge=6)
ax.text(x0 + w + 4, y0 + 8, "Mitte (+) frei lassen", fontsize=8.5, va="center", color="#555")
pdf.savefig(fig); fig.savefig("steckplan-5.png", dpi=100); plt.close(fig)
pdf.close()
print("ok")
