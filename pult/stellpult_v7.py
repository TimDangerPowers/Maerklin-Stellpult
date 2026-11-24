"""Stellpult v7 (Stand 21.11. abends): OLED per 4 Schrauben, Kappen 10/13 mm, Brücke als Überführung, Gehäuse 55 mm hoch.
Stellpult v6 (= v5 + 1,3"-OLED-Display SH1106 unten zwischen ANIMATION und STOP; AUTO/LICHT/ANIM etwas nach links)
Stellpult v5 (= v4, aber MÜHLE + QUALM -> ein Taster ANIMATION: Mühle, Qualm, Schweißlicht Fabrik): Gleisplan-Deckel, KY-004-Taster mit gedruckten Kappen, LED-Perlen aus der Lichterkette.

Teile:
  deckel         3 mm, Sichtseite oben. 0-0,6 mm WEISS drucken, ab 0,6 mm SCHWARZ (Filamentwechsel).
                 Gleise, Pfeile, Signale und Schrift sind Schlitze bis auf die weiße Schicht.
  traegerplatte  2 mm, schwarz, liegt direkt unter dem Deckel. Unten dran (beim Druck oben):
                 - viereckige LED-Halter: Perle von unten bis zum Anschlag reinstecken, Kabel in den Schlitzen
                 - je 2 Dome pro Taster (M2,5 selbstschneidend)
                 Wird mit den 6 Eckschrauben zusammen mit dem Deckel auf das Gehäuse geschraubt.
  tasterbruecke  16x: Halter für ein KY-004 (Platine 13x17), Platine von der Pin-Seite einschieben, 2 Klemmschrauben
                 M2,5 an den Pin-Ecken drücken sie fest. Mit 2 Schrauben M2,5 x 8 an die Domspitzen, Taster zeigt zum Deckel.
  v7.2: Trägerplatte wird gespiegelt exportiert (wird zum Einbau umgedreht). STOP-Dome quer.
  kappe-10 / kappe-stop-13  Tasterkappen (v6 kleiner) (Kopf nach unten drucken).
  distanzscheibe 1 mm, nur falls ein Taster schon ohne Drücken auslöst (zwischen Dom und Brücke).
  gehaeuse       Wanne, Säulen 2 mm kürzer als v3 (Platz für die Trägerplatte).
Aufruf: python stellpult_v7.py [ausgabeordner]
"""
import math, sys
from pathlib import Path
import numpy as np
import cadquery as cq

W, H = 350.0, 185.0
T, DIFF = 3.0, 0.6
SLOT = 2.6
HB, WALL, BOT = 55.0, 2.4, 2.0      # v6: 13 mm höher, Platz für Dupont-Stecker unter den Tastern (Stifte nach unten)
SPLIT = W / 2                 # Deckel + Gehäuse
FUGE_D = 8.0                  # v7.1: Fugen-Dome nicht mehr halbiert, sondern je ein ganzer Dom links und rechts der Fuge
CORNER = [(6, 6), (W-6, 6), (6, H-6), (W-6, H-6), (SPLIT - FUGE_D, 6), (SPLIT + FUGE_D, 6), (SPLIT - FUGE_D, H-6), (SPLIT + FUGE_D, H-6)]
LASCHE_Y = [55.0, 130.0]      # Verbinderlaschen innen am Boden über der Fuge
LASCHE_DX = 12.0

# ---- Trägerplatte / LED / Taster ----
TP = 2.0                       # Dicke Trägerplatte
PERLE = 5.4                    # Durchmesser LED-Perle (Laternen-Lichterkette)
HALTER_I = PERLE + 0.4         # (alt, quadratisch)
HALTER_X, HALTER_Y = 6.4, 11.4 # v7.1: Perle im Heißkleber-Tropfen 6 x 11 mm, Kabel läuft in y
HALTER_QUER = {"AUTO", "LICHT", "ANIM"}   # diese Halter liegen quer (Kabel in x), sonst stoßen sie an die Taster
HALTER_W, HALTER_T = 1.2, 8.0  # Wand, Tiefe unter der Platte
LICHTLOCH = 4.2
# KY-004 (Funduino: 18,2 x 14,6 mm Platine)
PCB_L, PCB_B, PCB_D = 17.0, 13.0, 1.6    # Tim gemessen 24.11. (ohne Pins)
SW_H = 6.6                     # Platine-Oberseite bis Tasterknopf: Tim gemessen 6,5 (gedrückt 6,0) -> 0,1 Luft
SPIEL = 0.3                    # Luft Kappenkragen -> Deckel
KAPPE_D, KAPPE_STOP_D = 10.0, 13.0
KRAGEN, KRAGEN_T = 3.0, 3.0    # Kragen: 45°-Kegel unter dem Deckel, 3 mm breiter, 3 mm hoch (stützenfrei)
UEBERSTAND = 2.0               # Kappe steht 2 mm über dem Deckel
STIEL_D, STIEL_L, FUSS_D = 7.0, 4.0, 8.0
DOM_D, DOM_LOCH, DOM_ABST = 6.5, 2.2, 14.0
BAR_T = 2.5
Z_KRAGEN_U = -(SPIEL + KRAGEN_T)            # Unterkante Kragen (z=0 = Deckel-Unterseite)
Z_KNOPF = Z_KRAGEN_U - STIEL_L
Z_BAR = Z_KNOPF - SW_H - PCB_D              # Oberseite Brücke = Unterseite Platine
DOM_L = -Z_BAR - TP

def arc(cx, cy, r, a0, a1, n=30):
    t = np.radians(np.linspace(a0, a1, n)); return list(zip(cx + r*np.cos(t), cy + r*np.sin(t)))
Y1, Y2, Y3, Y4 = 130, 100, 70, 42
GLEISE = [
    arc(55, 82, 28, 90, 360, 60),
    [(72, 110), (84, 110), (92, 112), (100, 124), (104, 130)],
    [(114, 130), (292, 130)],          # Lücke: Gleis 1 läuft unter der Brücke durch
    [(83, 82), (95, 100), (108, 125), (116, 145), (130, 165)],
    [(130, 165), (325, 165)],
    [(292, 130)] + arc(292, 105, 25, 90, 0, 20)[1:],
    arc(330, 105, 13, 180, 360, 30),
    [(343, 105), (343, 152)] + arc(330, 152, 13, 0, 90, 15)[1:],
    [(145, 130), (165, Y2), (250, Y2), (270, 130)],
    [(205, Y2), (222, Y3), (290, Y3)],
    [(255, Y3), (270, Y4), (292, Y4)],
]
TUNNEL = [((55 + i*4.0, 110), (57.5 + i*4.0, 110)) for i in range(4)]
STRICHE = []    # v6: keine Kürzungs-/Brückenstriche mehr, Brücke = Lücke im unteren Gleis
PRELL = [(293, Y3), (295, Y4)]

# Leuchtpunkte (Name = Firmware PultLed)
PIX = {
    "AUTO": ((22, 41), "punkt", None), "LICHT": ((60, 41), "punkt", None), "ANIM": ((98, 41), "punkt", None),
    "W1_G": ((130, 115), "pfeil", (1, 0)), "W1_A": ((141, 115), "pfeil", (1, -1.5)),
    "S2": ((178, 111), "punkt", None), "S1": ((178, 140), "punkt", None),
    "W2_G": ((238, 145), "pfeil", (-1, 0)), "W2_A": ((249, 145), "pfeil", (-1, -1.5)),
    "E": ((236, 86), "blitz", None),
    "W3_G": ((228, 57), "pfeil", (1, 0)), "W3_A": ((239, 57), "pfeil", (1, -1.6)),
    "W4_G": ((276, 57), "pfeil", (1, 0)), "W4_A": ((287, 57), "pfeil", (1, -1.9)),
    "T1": ((327, 70), "blitz", None), "T2": ((327, 30), "blitz", None),
}
# Taster: name -> (x, y, Ausrichtung der Dome "x"/"y", Kappe, Beschriftung (text, x, y) oder None)
TASTER = {
    "W1": (141, 148, "x", KAPPE_D, ("W1", 141, 136)),
    "W2": (273.5, 147, "x", KAPPE_D, ("W2", 273.5, 135)),
    "W3": (198, 55, "x", KAPPE_D, ("W3", 198, 43)),
    "W4": (263, 28, "x", KAPPE_D, ("W4", 263, 16)),
    "S1_G": (196, 148, "y", KAPPE_D, ("S1", 208, 158.5)),
    "S1_R": (220, 148, "y", KAPPE_D, None),
    "S2_G": (196, 110, "y", KAPPE_D, ("S2", 208, 120.5)),
    "S2_R": (220, 110, "y", KAPPE_D, None),
    "E": (260, 86, "x", KAPPE_D, ("E", 260, 74)),
    "T1": (310, 70, "y", KAPPE_D, ("T1", 310, 58.5)),
    "T2": (310, 30, "y", KAPPE_D, ("T2", 310, 18.5)),
    "AUTO": (22, 24, "x", KAPPE_D, ("AUTO", 22, 11)),
    "LICHT": (60, 24, "x", KAPPE_D, ("LICHT", 60, 11)),
    "ANIM": (98, 24, "x", KAPPE_D, ("ANIMATION", 98, 11)),
    "STOP": (205, 24, "y", KAPPE_STOP_D, ("STOP", 228, 24)),
}

# ---- OLED 1,3" SH1106 (BerryBase OLED-12864-B), Maße laut Hersteller-Zeichnung ----
# Platine 35,4 x 33,5, 4 Eckbohrungen 2,5 mm vom Rand (Raster 30,4 x 28,5), Stiftleiste oben (2 mm vom Rand, Stifte nach hinten),
# Flachkabel unten mittig 14 mm breit. Glas liegt vorne, ca. 23 mm hoch, mittig.
# Befestigung: Platine liegt mit den Ecken hinten auf der Trägerplatte, 4 x M2,5 x 8 von hinten durch die Eckbohrungen,
# mit gedruckter Unterlegscheibe 3 mm, in Löcher in Trägerplatte + Deckel (Deckel-Sichtseite bleibt zu).
OLED_X, OLED_Y = 141.0, 27.0
OLED_B, OLED_H = 35.4, 33.5
OLED_LOCH_DX, OLED_LOCH_DY = 30.4/2, 28.5/2
GLAS_B, GLAS_H = 35.4 + 0.8, 23.4 + 0.8                 # Ausschnitt Trägerplatte fürs Glas
FPC_B = 16.0                                           # Ausschnitt fürs Flachkabel unten
STIFT_B, STIFT_T, STIFT_DY = 14.0, 4.0, OLED_H/2 - 2.0 # Ausschnitt für die Lötpunkte der Stiftleiste
FENSTER_B, FENSTER_H, FENSTER_DY = 31.0, 17.0, 2.0     # sichtbares Feld im Deckel (laut Produktfoto ca. 2 mm Richtung Stiftleiste)
SCHEIBE_H = 3.0
DECKEL_RESTHAUT = 0.6                                  # so viel bleibt vorne über dem Schraubloch im Deckel

# ---------------- Hilfen ----------------
def seg(p, q, w, z0, h):
    L = math.dist(p, q); a = math.degrees(math.atan2(q[1]-p[1], q[0]-p[0]))
    s = cq.Workplane("XY").box(L, w, h, centered=(False, True, False)).rotate((0,0,0),(0,0,1),a).translate((p[0], p[1], z0))
    return s.union(cq.Workplane("XY").circle(w/2).extrude(h).translate((q[0], q[1], z0)))

def form(x, y, f, d, z0, h):
    if f == "punkt": return cq.Workplane("XY").circle(3.6).extrude(h).translate((x, y, z0))
    if f == "blitz":
        pts = [(0.9, 4.2), (-2.4, 0), (0.2, 0), (-0.9, -4.2), (2.4, 0.5), (-0.2, 0.5)]
        return cq.Workplane("XY").polyline([(x+a, y+b) for a, b in pts]).close().extrude(h).translate((0, 0, z0))
    dx, dy = d; n = math.hypot(dx, dy); dx, dy = dx/n, dy/n; px, py = -dy, dx
    L = 3.0
    s = seg((x-dx*L, y-dy*L), (x+dx*(L-1.5), y+dy*(L-1.5)), 1.6, z0, h)
    tip = (x+dx*(L+1.2), y+dy*(L+1.2)); b = (x+dx*(L-1.8), y+dy*(L-1.8))
    tri = cq.Workplane("XY").polyline([tip, (b[0]+px*2.4, b[1]+py*2.4), (b[0]-px*2.4, b[1]-py*2.4)]).close().extrude(h).translate((0, 0, z0))
    return s.union(tri)

SCHRIFT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
def text(t, x, y, size, z0, h):
    # Inter Black: dicke Striche (>= 0,8 mm), damit die Düse 0,4 die Buchstaben sauber druckt
    return cq.Workplane("XY").text(t, size, h, fontPath=SCHRIFT, halign="center", valign="center").translate((x, y, z0))

def loch_d(k): return k + 0.4

# ---------------- Deckel ----------------
def deckel():
    d = cq.Workplane("XY").rect(W, H, centered=False).extrude(T).edges("|Z").fillet(6)
    z0, h = DIFF, T
    cut = []
    for P in GLEISE:
        cut.append(cq.Workplane("XY").circle(SLOT/2).extrude(h).translate((P[0][0], P[0][1], z0)))
        for p, q in zip(P, P[1:]): cut.append(seg(p, q, SLOT, z0, h))
    for p, q in TUNNEL: cut.append(seg(p, q, SLOT, z0, h))
    for p, q in STRICHE: cut.append(seg(p, q, 1.2, z0, h))
    for x, y in PRELL: cut.append(cq.Workplane("XY").box(2.6, 9, h, centered=(True, True, False)).translate((x, y, z0)))
    for (x, y), f, dd in PIX.values(): cut.append(form(x, y, f, dd, z0, h))
    for n, (x, y, o, k, lbl) in TASTER.items():
        if lbl: cut.append(text(lbl[0], lbl[1], lbl[2], 5.0 if len(lbl[0]) < 4 else 4.4, z0, h))
    cut.append(text("BERG", 55, 82, 5, z0, h))
    for c in cut: d = d.cut(c)
    for n, (x, y, o, k, lbl) in TASTER.items():
        d = d.cut(cq.Workplane("XY").circle(loch_d(k)/2).extrude(T + 2).translate((x, y, -1)))
    d = d.cut(cq.Workplane("XY").box(FENSTER_B, FENSTER_H, T + 2).edges("|Z").fillet(1.5).translate((OLED_X, OLED_Y + FENSTER_DY, T/2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            d = d.cut(cq.Workplane("XY").circle(1.1).extrude(T - DECKEL_RESTHAUT).translate((OLED_X + sx*OLED_LOCH_DX, OLED_Y + sy*OLED_LOCH_DY, -0.01)))   # von unten (z=0 liegt auf der Trägerplatte), oben (Sichtseite) bleibt zu
    for x, y in CORNER:
        d = d.cut(cq.Workplane("XY").circle(1.7).extrude(T + 2).translate((x, y, -1)))
        d = d.cut(cq.Workplane("XY").circle(3.2).extrude(1.6).translate((x, y, T-1.6+0.01)))
    return d

# ---------------- Trägerplatte ----------------
# Koordinaten der Platte im DRUCK: z=0 ist die Seite am Deckel, Aufbauten zeigen nach +z
PLATTE_X0, PLATTE_Y0 = WALL + 0.5, WALL + 0.5
PW, PH = W - 2*PLATTE_X0, H - 2*PLATTE_Y0

def dome_pos(x, y, o):
    return [(x - DOM_ABST, y), (x + DOM_ABST, y)] if o == "x" else [(x, y - DOM_ABST), (x, y + DOM_ABST)]

def halter(x, y, quer=False):
    ax, ay = HALTER_X + 2*HALTER_W, HALTER_Y + 2*HALTER_W
    hx, hy = HALTER_X, HALTER_Y
    if quer: ax, ay, hx, hy = ay, ax, hy, hx
    h = cq.Workplane("XY").box(ax, ay, HALTER_T, centered=(True, True, False)).translate((x, y, TP))
    h = h.cut(cq.Workplane("XY").box(hx, hy, HALTER_T + 1, centered=(True, True, False)).translate((x, y, TP)))
    # Kabelschlitze in zwei gegenüberliegenden Wänden (von unten bis 2,5 mm vor die Platte)
    s = cq.Workplane("XY").box(ax + 2 if quer else 2.4, 2.4 if quer else ay + 2, HALTER_T - 2.5, centered=(True, True, False)).translate((x, y, TP + 2.5))
    h = h.cut(s)
    return h

def traegerplatte():
    p = cq.Workplane("XY").rect(PW, PH, centered=False).extrude(TP).edges("|Z").fillet(4).translate((PLATTE_X0, PLATTE_Y0, 0))
    for n, ((x, y), f, dd) in PIX.items():
        p = p.union(halter(x, y, n in HALTER_QUER))
        p = p.cut(cq.Workplane("XY").circle(LICHTLOCH/2).extrude(TP + 2).translate((x, y, -1)))
    for n, (x, y, o, k, lbl) in TASTER.items():
        for dx, dy in dome_pos(x, y, o):
            p = p.union(cq.Workplane("XY").circle(DOM_D/2).extrude(TP + DOM_L).translate((dx, dy, 0)))
            p = p.cut(cq.Workplane("XY").circle(DOM_LOCH/2).extrude(DOM_L).translate((dx, dy, TP + 0.6)))
        p = p.cut(cq.Workplane("XY").circle((k + 2*KRAGEN + 1)/2).extrude(TP + 2).translate((x, y, -1)))
    def ausschnitt(b, h, dy):
        return cq.Workplane("XY").box(b, h, TP + 2, centered=(True, True, False)).translate((OLED_X, OLED_Y + dy, -1))
    p = p.cut(ausschnitt(GLAS_B, GLAS_H, 0))
    p = p.cut(ausschnitt(FPC_B, OLED_H/2 - GLAS_H/2 + 1, -(GLAS_H/2 + (OLED_H/2 - GLAS_H/2 + 1)/2) + 0.5))
    p = p.cut(ausschnitt(STIFT_B, STIFT_T, STIFT_DY))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = p.cut(cq.Workplane("XY").circle(1.1).extrude(TP + 2).translate((OLED_X + sx*OLED_LOCH_DX, OLED_Y + sy*OLED_LOCH_DY, -1)))
    # flacher Rand (1 mm) als Anschlag zum Ausrichten
    r = cq.Workplane("XY").box(OLED_B + 0.8 + 2.4, OLED_H + 0.8 + 2.4, 1.0, centered=(True, True, False)).translate((OLED_X, OLED_Y, TP))
    r = r.cut(cq.Workplane("XY").box(OLED_B + 0.8, OLED_H + 0.8, 2, centered=(True, True, False)).translate((OLED_X, OLED_Y, TP - 0.5)))
    p = p.union(r)
    for x, y in CORNER:
        p = p.cut(cq.Workplane("XY").circle(1.7).extrude(TP + 2).translate((x, y, -1)))
    return p

# ---------------- Tasterbrücke (Druck: Steg auf dem Bett, Rand nach oben) ----------------
LIPPE = 1.0
KLEMM_DX = 1.4      # v7.2: Klemmschraube M2,5 an der Pin-Seite, Kopf (Ø 4,5) greift 0,85 mm über die Platinenecke
def tasterbruecke():
    hx, hy = PCB_B/2 + 0.15, PCB_L/2 + 0.15      # Tasche: Breite in x, Länge in y, Pins zeigen nach +y
    wand = 1.6
    rh = 3.0                                      # Randhöhe über dem Steg
    bar = cq.Workplane("XY").box(2*DOM_ABST + DOM_D + 2, 12, BAR_T, centered=(True, True, False))
    bar = bar.union(cq.Workplane("XY").box(2*(hx + wand), 2*(hy + wand), BAR_T, centered=(True, True, False)))
    rand = cq.Workplane("XY").box(2*(hx + wand), 2*(hy + wand), rh, centered=(True, True, False)).translate((0, 0, BAR_T))
    rand = rand.cut(cq.Workplane("XY").box(2*hx, 2*hy, 4, centered=(True, True, False)).translate((0, 0, BAR_T)))
    rand = rand.cut(cq.Workplane("XY").box(2*hx, 10, 4, centered=(True, True, False)).translate((0, hy + 3, BAR_T)))   # Pin-Seite offen
    b = bar.union(rand)
    # Klemmschrauben-Sockel: Oberkante = Platinen-Oberkante, damit der Schraubenkopf die Ecke festdrückt
    ky = hy - 2.6
    for sx in (-1, 1):
        sock = cq.Workplane("XY").circle(3.2).extrude(BAR_T + PCB_D).translate((sx*(hx + KLEMM_DX), ky, 0))
        b = b.union(sock)
        b = b.cut(cq.Workplane("XY").box(7, 10, 5, centered=(True, True, False)).translate((sx*(hx + KLEMM_DX), ky + 2, BAR_T + PCB_D)))  # Rand dort weg (bis zum Ende)
    b = b.cut(cq.Workplane("XY").box(2*hx, 2*hy, 4, centered=(True, True, False)).translate((0, 0, BAR_T)))   # Tasche wieder frei
    # Leisten über den Längskanten (0,6 Luft für Lötstellen), an der Pin-Seite 6 mm kürzer für die Klemmschrauben
    lz = BAR_T + PCB_D + 0.6
    for sx in (-1, 1):
        b = b.union(cq.Workplane("XY").box(LIPPE, 2*hy - 6, rh - PCB_D - 0.6, centered=(True, True, False)).translate((sx*(hx - LIPPE/2), -3, lz)))
    for sx in (-1, 1):
        b = b.cut(cq.Workplane("XY").circle(1.1).extrude(BAR_T + PCB_D + 1).translate((sx*(hx + KLEMM_DX), ky, -0.5)))
    # Fenster für Lötstellen unten: Platine liegt nur auf 1,2 mm Rand rundum auf, Pin-Seite offen
    b = b.cut(cq.Workplane("XY").box(2*hx - 2.4, 2*hy - 1.2 + 5, BAR_T + 2, centered=(True, True, False)).translate((0, 0.6 + 2.5, -1)))
    for sx in (-DOM_ABST, DOM_ABST):
        b = b.cut(cq.Workplane("XY").circle(1.45).extrude(BAR_T + 2).translate((sx, 0, -1)))
    return b

def oledscheibe():
    """Unterlegscheibe für M2,5 x 8 am Display (4 Stück)."""
    return cq.Workplane("XY").circle(3.0).circle(1.45).extrude(SCHEIBE_H)

def kappe(d):
    """Kopf nach unten drucken. Höhen: Kopf (Überstand + Deckel + Spiel), Kragen, Stiel."""
    kopf_h = UEBERSTAND + T + SPIEL
    k = cq.Workplane("XY").circle(d/2).extrude(kopf_h).edges("<Z").chamfer(0.6)
    kr = cq.Workplane("XY").circle(d/2).workplane(offset=KRAGEN_T).circle(d/2 + KRAGEN).loft()
    kr = cq.Workplane("XY").add(kr.val()).translate((0, 0, kopf_h))
    kr2 = cq.Workplane("XY").circle(d/2 + KRAGEN).extrude(0.01).translate((0, 0, kopf_h + KRAGEN_T - 0.01))
    st = cq.Workplane("XY").circle(STIEL_D/2).extrude(STIEL_L).translate((0, 0, kopf_h + KRAGEN_T))
    fu = cq.Workplane("XY").circle(FUSS_D/2).extrude(1.0).translate((0, 0, kopf_h + KRAGEN_T + STIEL_L - 1.0))
    return k.union(kr).union(kr2).union(st).union(fu)

def distanzscheibe():
    return cq.Workplane("XY").circle(DOM_D/2).circle(1.5).extrude(1.0)

def gehaeuse():
    g = cq.Workplane("XY").rect(W, H, centered=False).extrude(HB).edges("|Z").fillet(6)
    g = g.cut(cq.Workplane("XY").rect(W-2*WALL, H-2*WALL, centered=False).extrude(HB).edges("|Z").fillet(6-WALL).translate((WALL, WALL, BOT)))
    for x, y in CORNER:
        g = g.union(cq.Workplane("XY").circle(4.5).extrude(HB - TP - BOT).translate((x, y, BOT)))
        g = g.cut(cq.Workplane("XY").circle(1.25).extrude(HB).translate((x, y, BOT + 2)))
    g = g.cut(cq.Workplane("XY").box(60, WALL+2, 14, centered=(True, True, False)).translate((W*0.62, H-WALL/2, HB-14-TP)))
    g = g.cut(cq.Workplane("XY").box(14, WALL+2, 8, centered=(True, True, False)).translate((W*0.25, H-WALL/2, 8)))
    for y in LASCHE_Y:                                   # Dome für die Verbinderlaschen (Schraube 3x10)
        for sx in (-1, 1):
            g = g.union(cq.Workplane("XY").circle(4.0).extrude(6.0).translate((SPLIT + sx*LASCHE_DX, y, BOT)))
            g = g.cut(cq.Workplane("XY").circle(1.25).extrude(6.0).translate((SPLIT + sx*LASCHE_DX, y, BOT + 0.6)))
    for x, y in [(15, 15), (W-15, 15), (15, H-15), (W-15, H-15), (SPLIT - 15, 15), (SPLIT + 15, 15), (SPLIT - 15, H-15), (SPLIT + 15, H-15)]:
        g = g.cut(cq.Workplane("XY").circle(5.2).extrude(0.8).translate((x, y, -0.01)))
    return g

def lasche():
    """Verbinder über der Gehäusefuge innen am Boden, 2 Stück, flach drucken."""
    l = cq.Workplane("XY").box(2*LASCHE_DX + 10, 12, 3.0, centered=(True, True, False)).edges("|Z").fillet(2)
    for sx in (-1, 1):
        l = l.cut(cq.Workplane("XY").circle(1.7).extrude(5).translate((sx*LASCHE_DX, 0, -1)))
    return l

def halb(s, links, sx=SPLIT):
    big = 1000
    return s.intersect(cq.Workplane("XY").box(big, big, big).translate(((sx - big/2) if links else (sx + big/2), 0, 0)))

# ---------------- 2D-Prüfung (Kollisionen unter dem Deckel) ----------------
def fussabdruecke():
    from shapely.geometry import Point, box as sbox
    from shapely.affinity import rotate, translate
    teile = []
    ax, ay = HALTER_X + 2*HALTER_W, HALTER_Y + 2*HALTER_W
    for n, ((x, y), f, dd) in PIX.items():
        bx, by = (ay, ax) if n in HALTER_QUER else (ax, ay)
        teile.append(("LED " + n, sbox(x - bx/2, y - by/2, x + bx/2, y + by/2)))
    for n, (x, y, o, k, lbl) in TASTER.items():
        hx, hy = PCB_B/2 + 0.15 + 1.6 + 2.0, PCB_L/2 + 0.15 + 1.6   # +2 für Klemmsockel
        g = sbox(-(DOM_ABST + DOM_D/2 + 1), -6, DOM_ABST + DOM_D/2 + 1, 6).union(sbox(-hx, -hy, hx, hy))
        if o == "y": g = rotate(g, 90, origin=(0, 0))
        teile.append(("Taster " + n, translate(g, x, y)))
    teile.append(("OLED", sbox(OLED_X - OLED_B/2 - 1.6, OLED_Y - OLED_H/2 - 1.6, OLED_X + OLED_B/2 + 1.6, OLED_Y + OLED_H/2 + 1.6)))
    for x, y in CORNER:
        teile.append(("Säule", Point(x, y).buffer(5.0)))
    rand = sbox(PLATTE_X0 + 0.5, PLATTE_Y0 + 0.5, PLATTE_X0 + PW - 0.5, PLATTE_Y0 + PH - 0.5)
    return teile, rand

def pruefe():
    teile, rand = fussabdruecke()
    probleme = []
    for i, (n1, g1) in enumerate(teile):
        if not rand.contains(g1) and n1 != "Säule": probleme.append(f"{n1} ragt über den Plattenrand")
        for n2, g2 in teile[i+1:]:
            dist = g1.distance(g2)
            if dist < 0.8: probleme.append(f"{n1} <-> {n2}: Abstand {dist:.1f} mm")
    return probleme, teile

def plattenschnitt(teile):
    """Schnittstelle der Trägerplatte: frei von Teilen, beide Hälften <= 255 mm."""
    from shapely.geometry import LineString
    best = None
    for sx in np.arange(100, 250, 0.5):
        l = LineString([(sx, 0), (sx, H)])
        d = min(g.distance(l) for n, g in teile)
        if PLATTE_X0 + PW - sx > 255 or sx - PLATTE_X0 > 255: continue
        if abs(sx - SPLIT) < 15: continue                  # nicht auf der Deckelfuge
        if best is None or d > best[1]: best = (sx, d)
    return best

# ---------------- LED-Kette: Reihenfolge, Perlenabstand 10 cm ----------------
REIHENFOLGE = ["AUTO", "LICHT", "ANIM", "W1_G", "W1_A", "S2", "S1", "W2_G", "W2_A",
               "E", "W3_G", "W3_A", "W4_G", "W4_A", "T2", "T1"]
MAX_SPRUNG = 70.0      # mm Luftlinie, die eine 10-cm-Strecke unter dem Deckel sicher schafft

def kette():
    perle, liste = 0, []
    for i, n in enumerate(REIHENFOLGE):
        if i:
            dist = math.dist(PIX[REIHENFOLGE[i-1]][0], PIX[n][0])
            perle += 1 + int(dist // MAX_SPRUNG)    # bei langen Wegen eine Perle frei lassen
        liste.append((n, perle))
    return liste

if __name__ == "__main__":
    probleme, teile = pruefe()
    print("Kollisionen:", probleme or "keine")
    print("Plattenschnitt:", plattenschnitt(teile))
    print("Kette:", kette())
    print("Dom-Länge:", round(DOM_L, 2), "Brücke z:", round(Z_BAR, 2))

def druck_spiegeln(teil):
    """v7.2: Trägerplatte wird mit Domen nach oben gedruckt und zum Einbau umgedreht.
    Damit Löcher/Halter danach unter den Deckel passen, wird sie in y gespiegelt exportiert."""
    return teil.mirror("XZ").translate((0, H, 0))

def export_all(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    probleme, teile = pruefe()
    assert not probleme, probleme
    PS = plattenschnitt(teile)[0]
    for name, fn, sx in (("deckel", deckel, SPLIT), ("traegerplatte", traegerplatte, PS), ("gehaeuse", gehaeuse, SPLIT)):
        s = fn()
        if name == "traegerplatte": s = druck_spiegeln(s)
        cq.exporters.export(s, str(out / f"ganz-{name}.stl"), tolerance=0.05, angularTolerance=0.2)
        for seite, links in (("links", True), ("rechts", False)):
            h = halb(s, links, sx)
            cq.exporters.export(h, str(out / f"{name}-{seite}.stl"), tolerance=0.05, angularTolerance=0.2)
            bb = h.val().BoundingBox(); print(name, seite, round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1))
    for name, s in (("tasterbruecke", tasterbruecke()), ("kappe-10", kappe(KAPPE_D)), ("kappe-stop-13", kappe(KAPPE_STOP_D)),
                    ("distanzscheibe-1mm", distanzscheibe()), ("oled-scheibe-3mm", oledscheibe()), ("verbinderlasche", lasche())):
        cq.exporters.export(s, str(out / f"{name}.stl"), tolerance=0.02, angularTolerance=0.1)
        bb = s.val().BoundingBox(); print(name, round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1))
