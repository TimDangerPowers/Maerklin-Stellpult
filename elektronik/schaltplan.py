"""Schaltplan Märklin-Fensterbahn: Box unter dem Berg + Stellpult + Märklin-Anschlüsse -> schaltplan.pdf / .png"""
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages
C = {"5V": "#d62728", "3V3": "#ff7f0e", "GND": "#222222", "SDA": "#1f77b4", "SCL": "#17becf", "DAT": "#2ca02c",
     "GELB": "#e6b800", "BRAUN": "#8c564b", "ROT": "#c0392b", "BLAU": "#3060c0", "230": "#7f7f7f", "SIG": "#9467bd"}
def box(ax, x, y, w, h, title, lines=(), fc="#f4f4f4", ec="#333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=1.3))
    ax.text(x + w/2, y + h - 1.6, title, ha="center", va="top", fontsize=9, weight="bold")
    for i, l in enumerate(lines): ax.text(x + 1, y + h - 5 - i*2.6, l, fontsize=6.6, va="top")
def wire(ax, pts, net, lab=None, lw=1.6, at=0.5, dy=0.8):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=C[net], lw=lw, solid_capstyle="round")
    if lab:
        i = max(0, int((len(pts)-1)*at)); a, b = pts[i], pts[i+1] if i+1 < len(pts) else pts[i]
        ax.text((a[0]+b[0])/2, (a[1]+b[1])/2 + dy, lab, fontsize=6, color=C[net], ha="center", weight="bold",
                bbox=dict(fc="white", ec="none", pad=.3, alpha=.85))
def legend(fig, y=.04):
    items = [("5 V", "5V"), ("3,3 V", "3V3"), ("GND / Masse", "GND"), ("I²C SDA", "SDA"), ("I²C SCL", "SCL"), ("LED-Daten", "DAT"),
             ("Märklin gelb (16 V ~)", "GELB"), ("Märklin braun (0)", "BRAUN"), ("Märklin rot (Fahrstrom)", "ROT"), ("blaue Spulenkabel", "BLAU"), ("230 V", "230")]
    for i, (t, n) in enumerate(items):
        x = .03 + (i % 6) * .16; yy = y + (0 if i < 6 else -.025)
        fig.add_artist(plt.Line2D([x, x + .025], [yy + .006]*2, color=C[n], lw=3)); fig.text(x + .03, yy, t, fontsize=7.5)
with PdfPages("schaltplan.pdf") as pdf:
    # ---------------- Seite 1: Strom + Logik ----------------
    fig = plt.figure(figsize=(16.54, 11.69)); ax = fig.add_axes([.02, .09, .96, .84]); ax.set_xlim(0, 200); ax.set_ylim(0, 140); ax.axis("off")
    fig.text(.03, .955, "Schaltplan 1/3 – Strom und Steuerung (Box unter dem Berg + Stellpult)", fontsize=17, weight="bold")
    fig.text(.03, .935, "Alle 5-V-Masse-Leitungen (GND) sind miteinander verbunden. Die Märklin-Seite (Trafo) bleibt davon getrennt, die Relais trennen beides. Verteilung mit WAGO-Klemmen.", fontsize=9, color="#555")
    ax.add_patch(FancyBboxPatch((2, 28), 136, 108, boxstyle="round,pad=0.5", fc="none", ec="#999", ls="--")); ax.text(4, 134, "ELEKTRONIK-BOX (unter dem Berg)", fontsize=10, color="#777", weight="bold")
    ax.add_patch(FancyBboxPatch((146, 28), 52, 108, boxstyle="round,pad=0.5", fc="none", ec="#999", ls="--")); ax.text(148, 134, "STELLPULT", fontsize=10, color="#777", weight="bold")
    box(ax, 4, 104, 26, 26, "WAGO 5 V", ["221-415 (5-fach)", "verteilt 5 V an alle", "Teile mit „← 5 V“"], fc="#fdecec")
    box(ax, 4, 66, 26, 30, "WAGO GND", ["221-420 (10-fach)", "verteilt GND an alle", "Teile mit „GND“", "", "NICHT mit Märklin", "braun verbinden"], fc="#eeeeee")
    box(ax, 40, 98, 40, 32, "ESP32 WROOM-32 + Shield", ["5V ← 5 V · GND", "GPIO 21 / 22 = SDA / SCL", "GPIO 14 → LLC LV1 (Pult-LEDs)", "GPIO 2  → LLC LV2 (Häuser)", "3V3 → LLC LV + Kabel Ader 3"], fc="#e3eefc")
    box(ax, 90, 100, 44, 30, "MCP23017 Soldered (Relais)", ["VCC ← 5 V · GND", "SDA / SCL ← LLC2 HV1 / HV2 (5 V)", "GPA0–7 → RELM IN1–8", "GPB0–7 → RELM IN9–16", "(Adresse automatisch, Firmware sucht)"], fc="#e3eefc")
    box(ax, 40, 62, 22, 28, "2 × Pegelwandler LLC", ["LV ← 3,3 V · HV ← 5 V · GND", "LLC1: GPIO 14 → HV1", "LLC1: GPIO 2 → HV2", "LLC2: ESP SDA/SCL (LV)", "  ↔ Relais-MCP (HV)"], fc="#e8f6e8")
    box(ax, 67, 62, 22, 28, "8er-Relais", ["entfällt (v7.1):", "Mühle + Qualm laufen", "über das 16er", "(IN15 / IN16).", "", "GPIO 32/33 frei"], fc="#fff4dc")
    box(ax, 94, 32, 40, 58, "Relaisplatte RELM-16", ["(schaltet bei LOW)", "VCC + JD-VCC ← 5 V · GND", "IN1  Puls (Sicherheit)", "IN2/3  W1 gerade / abzweig", "IN4/5  W2 gerade / abzweig", "IN6/7  W3 gerade / abzweig", "IN8/9  W4 gerade / abzweig", "IN10/11 S1 rot / grün", "IN12/13 S2 rot / grün", "IN14 Entkuppler E", "IN15 Mühle · IN16 Qualm", "", "Kontakte: siehe Seite 2"], fc="#fff4dc")
    box(ax, 150, 93, 44, 37, "MCP23017 im Pult (Funduino)", ["VCC ← 3,3 V (Ader 3) · GND (Ader 2)", "SDA / SCL ← Ader 4 / 5", "A0, A1, A2 → GND · RESET → 3,3 V", "16 Taster KY-004: S → Eingang,", "„–“ → GND, Mitte frei", "A0–7: W1 W2 W3 W4 S1g S1r S2g S2r", "B0–7: E T1 T2 AUTO STOP LICHT ANIMATION (B7 frei)", "OLED 1,3\" daneben am selben Bus:", "  VCC 3,3 V · GND · SCL · SDA"], fc="#e3eefc")
    box(ax, 150, 66, 44, 22, "Pult-Anzeige (Lichterkette, 25 Perlen)", ["5 V ← Ader 1", "GND ← Ader 2", "Daten ← Ader 6"], fc="#e8f6e8")
    box(ax, 150, 32, 44, 24, "6-adriges Kabel Box ↔ Pult", ["max. 2 m", "1 = 5 V    2 = GND", "3 = 3,3 V  4 = SDA", "5 = SCL    6 = LED-Daten (LLC HV1)"], fc="#f4f4f4")
    box(ax, 4, 2, 30, 20, "Netzteil LRS-50-5", ["L ← braun (230 V)", "N ← blau (230 V)", "PE ← grün-gelb", "+V / −V = 5 V, 10 A"], fc="#fde2e2")
    box(ax, 40, 2, 40, 20, "Häuser (WS2812, 8 LEDs je Haus)", ["5 V + GND von den WAGOs", "Daten ← LLC HV2", "Haus 1 DOUT → Haus 2 DIN …"], fc="#e8f6e8")
    box(ax, 86, 2, 48, 20, "OLED-Display im Pult", ["VCC ← 3,3 V (Ader 3) · GND (Ader 2)", "SDA / SCL ← Ader 4 / 5", "(parallel zum Pult-MCP)"], fc="#e3eefc")
    # Netzteil -> WAGO
    wire(ax, [(34, 16), (36, 16), (36, 117), (30, 117)], "5V", "+V", at=.5, dy=0); wire(ax, [(34, 8), (33, 8), (33, 80), (30, 80)], "GND", "−V", at=.5, dy=0)
    # ESP -> MCP Relais (I2C)
    wire(ax, [(80, 118), (90, 118)], "SDA", "SDA", dy=1.2); wire(ax, [(80, 114), (90, 114)], "SCL", "SCL", dy=-2.6)
    wire(ax, [(112, 100), (112, 90)], "SIG", "16 Leitungen", dy=0)
    wire(ax, [(48, 100), (48, 90)], "DAT", "14 / 2", dy=0)
    wire(ax, [(51, 66), (51, 22)], "DAT", "Häuser (HV2)", at=.5, dy=0)
    # Kabelbündel Box -> Pult
    for k, net in enumerate(["5V", "GND", "3V3", "SDA", "SCL", "DAT"]):
        d = k * 0.9
        wire(ax, [(80, 104 - d), (86 - d, 104 - d), (86 - d, 95 - d), (140 + d, 95 - d), (140 + d, 44 - d*.6), (150, 44 - d*.6)], net, lw=1.2)
    ax.text(112, 96.5, "6-adriges Kabel zum Pult (5 V · GND · 3,3 V · SDA · SCL · LED-Daten)", ha="center", fontsize=6.5, weight="bold", color="#444", bbox=dict(fc="white", ec="none", pad=.3))
    for k, (net, y) in enumerate([("SDA", 108), ("DAT", 76)]):
        wire(ax, [(194, 44), (196.5, 44), (196.5, y), (194, y)], net, lw=1.2)
    ax.text(197.5, 60, "Ader 1–6", rotation=90, fontsize=6.5, va="center", color="#444")
    legend(fig); pdf.savefig(fig); fig.savefig("schaltplan-1.png", dpi=110); plt.close(fig)
    # ---------------- Seite 2: Märklin-Seite ----------------
    fig = plt.figure(figsize=(16.54, 11.69)); ax = fig.add_axes([.02, .09, .96, .84]); ax.set_xlim(0, 200); ax.set_ylim(0, 140); ax.axis("off")
    fig.text(.03, .955, "Schaltplan 2/3 – Märklin-Seite (Trafo, Weichen, Signale, Entkuppler, Mühle, Qualm)", fontsize=17, weight="bold")
    fig.text(.03, .935, "Nur das Puls-Relais gibt Masse (braun) auf die Spulen-Relais, immer nur ca. 0,2 s. Die Ruhekontakte (NC) bleiben frei: so wird nie eine falsche Spule mitgeschaltet.", fontsize=9, color="#555")
    box(ax, 4, 100, 30, 34, "Märklin-Trafo", ["gelb  = 16 V ~ (Licht/Magnetartikel)", "braun = Masse 0", "rot   = Fahrstrom (Regler)"], fc="#fff7d6")
    box(ax, 44, 124, 26, 10, "WAGO gelb", ["alle gelben Kabel"], fc="#fff7d6"); box(ax, 44, 110, 26, 10, "WAGO braun", ["Märklin-Masse"], fc="#f0e6df")
    box(ax, 44, 96, 26, 10, "WAGO rot", ["Fahrstrom"], fc="#fde2e2")
    wire(ax, [(34, 128), (44, 128)], "GELB", lw=2.5); wire(ax, [(34, 115), (44, 115)], "BRAUN", lw=2.5); wire(ax, [(34, 101), (44, 101)], "ROT", lw=2.5)
    # Puls
    box(ax, 80, 112, 22, 14, "Relais 1 = Puls", ["COM ← braun", "NO  → Puls-Schiene"], fc="#fff4dc")
    wire(ax, [(70, 114), (80, 114)], "BRAUN", lw=2.2)
    ax.add_patch(plt.Rectangle((106, 116), 90, 3, fc=C["BRAUN"], alpha=.35)); ax.text(151, 120.5, "Puls-Schiene (WAGO 221-420): COM von Relais 2–13", ha="center", fontsize=8, color=C["BRAUN"], weight="bold")
    wire(ax, [(102, 118), (106, 118)], "BRAUN", lw=2.2)
    names = [("2", "W1", "gerade"), ("3", "W1", "abzweig"), ("4", "W2", "gerade"), ("5", "W2", "abzweig"), ("6", "W3", "gerade"), ("7", "W3", "abzweig"),
             ("8", "W4", "gerade"), ("9", "W4", "abzweig"), ("10", "S1", "rot"), ("11", "S1", "grün"), ("12", "S2", "rot"), ("13", "S2", "grün")]
    for i, (r, a, d) in enumerate(names):
        x = 106 + i * 7.5
        box(ax, x, 92, 6.3, 18, f"R{r}", ["COM", "", "NO", "", "NC –"], fc="#fff4dc")
        wire(ax, [(x + 3.1, 116), (x + 3.1, 110)], "BRAUN", lw=1.4)
        wire(ax, [(x + 3.1, 92), (x + 3.1, 80)], "BLAU", lw=1.4)
        ax.text(x + 3.1, 78, f"{a}\n{d}", ha="center", va="top", fontsize=6.5, weight="bold")
    for j, (a, x0) in enumerate([("W1", 106), ("W2", 121), ("W3", 136), ("W4", 151), ("S1", 166), ("S2", 181)]):
        box(ax, x0, 50, 13.5, 18, a, ["2 blaue Kabel", "von oben", "gelb → WAGO", "gelb"], fc="#e9f0fb")
        wire(ax, [(x0 + 3.1, 72), (x0 + 3.1, 68)], "BLAU", lw=1.4); wire(ax, [(x0 + 10.6, 72), (x0 + 10.6, 68)], "BLAU", lw=1.4)
        wire(ax, [(x0 + 6.75, 50), (x0 + 6.75, 46), (57, 46), (57, 124)], "GELB", lw=1.2)
    box(ax, 4, 56, 34, 24, "Relais 14 = Entkuppler E", ["COM ← braun", "NO  → blaues Kabel Entkuppler", "gelb vom Entkuppler → WAGO gelb", "(ESP hält max. 3 s)"], fc="#fff4dc")
    wire(ax, [(46, 110), (46, 76), (38, 76)], "BRAUN", lw=1.4)
    box(ax, 4, 22, 34, 28, "Parkgleise T1 / T2", ["nicht geschaltet (normale Gleise).", "Fahrstrom rot wie gewohnt", "an die Gleis-Einspeisung.", "Taster T1/T2 im Pult haben", "vorerst keine Funktion."], fc="#fff4dc")
    wire(ax, [(50, 96), (50, 44), (38, 44)], "ROT", lw=1.4)
    box(ax, 4, 2, 64, 16, "16er-Relais 15 = Mühle, 16 = Qualm", ["COM ← gelb · NO → Kabel 1 von Mühle bzw. Rauchgenerator · Kabel 2 → braun", "Qualm schaltet die Firmware nach einiger Zeit automatisch ab."], fc="#fff4dc")
    wire(ax, [(62, 124), (62, 18)], "GELB", lw=1.2)
    box(ax, 76, 2, 60, 26, "Signale S1 / S2 (alte Märklin-Signale)", ["Das Signal schaltet seinen Halteabschnitt selbst:", "Mittelleiter vor dem Signal isolieren, die rote", "Fahrstrom-Leitung des Abschnitts kommt an den", "Signal-Kontakt (wie in der Signal-Anleitung).", "Grün = Fahrstrom an, Rot = Zug hält."], fc="#e9f0fb")
    legend(fig); pdf.savefig(fig); fig.savefig("schaltplan-2.png", dpi=110); plt.close(fig)
    # ---------------- Seite 3: Tabellen ----------------
    fig = plt.figure(figsize=(16.54, 11.69)); fig.text(.03, .955, "Schaltplan 3/3 – Belegung zum Abhaken", fontsize=17, weight="bold")
    T = [("ESP32", ["5V ← WAGO 5 V", "GND ← WAGO GND", "3V3 → Kabel Ader 3, LLC LV", "GPIO 21 → SDA (Kabel Ader 4 + LLC2)", "GPIO 22 → SCL (Kabel Ader 5 + LLC2)", "GPIO 14 → LLC LV1 (Pult-LEDs)", "GPIO 2 → LLC LV2 (Häuser)", "GPIO 5, 15, 32, 33 frei lassen", "SDA/SCL → LLC2 → Relais-MCP"]),
         ("Relais-MCP (Soldered) → RELM-16", ["GPA0 → IN1 Puls", "GPA1/2 → IN2/3 W1 gerade/abzweig", "GPA3/4 → IN4/5 W2", "GPA5/6 → IN6/7 W3", "GPA7 → IN8 W4 gerade", "GPB0 → IN9 W4 abzweig", "GPB1/2 → IN10/11 S1 rot/grün", "GPB3/4 → IN12/13 S2 rot/grün", "GPB5 → IN14 Entkuppler", "GPB6 → IN15 Mühle", "GPB7 → IN16 Qualm", "VCC → 5 V, GND → GND"]),
         ("Kabel Box ↔ Pult (6 Adern)", ["1  5 V", "2  GND", "3  3,3 V", "4  SDA", "5  SCL", "6  LED-Daten (LLC HV1)", "", "Im Pult: 5 V/GND/Daten → Lichterkette,", "3,3 V/GND/SDA/SCL → Pult-MCP + OLED"]),
         ("Märklin", ["Trafo gelb → WAGO gelb → alle gelben Kabel", "Trafo braun → WAGO braun → Puls-COM, E-COM,", "    Mühle/Qualm Rückleitung, Gleis-Masse", "WAGO braun NICHT mit WAGO GND verbinden", "Trafo rot → Gleis-Einspeisung (auch T1/T2)", "Relais 2–13: COM ← Puls-Schiene, NO → blau, NC frei", "Relais 14: COM ← braun, NO → Entkuppler blau", "Relais 15/16: COM ← gelb, NO → Mühle / Rauch"])]
    for i, (t, ls) in enumerate(T):
        x = .04 + (i % 2) * .48; y = .88 - (i // 2) * .44
        fig.text(x, y, t, fontsize=13, weight="bold")
        for j, l in enumerate(ls): fig.text(x, y - .035 - j * .03, ("☐ " if l.strip() else "") + l, fontsize=10.5)
    fig.text(.04, .03, "Stand 24.11.: ohne Schaltgleise (GPIO 5/15 frei lassen). Firmware v7 passt zu diesem Plan.", fontsize=9.5, color="#555")
    pdf.savefig(fig); fig.savefig("schaltplan-3.png", dpi=110); plt.close(fig)
