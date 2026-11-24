"""Elektronik-Box unter der Bergecke (P4, links), v2 mit 16er + 8er Relais: Haube (wird unter die Platte geschraubt) + Montageplatte (von unten, Module drauf).
Druck ohne Stützen: Haube mit der geschlossenen Seite aufs Bett, Platte flach, Abstandshalter stehend."""
import cadquery as cq, os
IW, ID, IH = 200.0, 232.0, 48.0      # Innenmaße
WD, TOP = 2.4, 3.0                   # Wand, Deckel (an der OSB)
PL = 4.0                             # Montageplatte
OW, OD = IW + 2*WD, ID + 2*WD
os.makedirs("box-stl", exist_ok=True)
# ---------- Haube ----------
h = cq.Workplane("XY").box(OW, OD, IH + TOP, centered=(True, True, False))
h = h.cut(cq.Workplane("XY").box(IW, ID, IH, centered=(True, True, False)).translate((0, 0, TOP)))
# Schraublöcher in der Decke (4 x 30 Spanplatte, Senkkopf) – Decke liegt beim Druck unten
for x, y in [(-70, -85), (70, -85), (-70, 85), (70, 85)]:
    h = h.cut(cq.Workplane("XY").center(x, y).circle(2.3).extrude(TOP + 1).translate((0, 0, -0.5)))
    h = h.cut(cq.Workplane("XY").workplane(offset=TOP - 2.0).center(x, y).circle(2.3).workplane(offset=2.01).circle(4.3).loft())
# Eck-Dome für die Platte (3 x 12 Schrauben von unten), 45°-Anschrägung unten -> stützenfrei
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = sx*(IW/2 - 5), sy*(ID/2 - 5)
        d = cq.Workplane("XY").center(cx, cy).rect(10, 10).extrude(IH - 1).translate((0, 0, TOP))
        d = d.cut(cq.Workplane("XY").center(cx, cy).circle(1.25).extrude(20).translate((0, 0, TOP + IH - 20)))
        h = h.union(d)
# Kabeldurchlässe am offenen Rand (U-Kerben, Platte schließt sie unten ab)
def kerbe(h, x, y, w, horiz):
    k = cq.Workplane("XY").box(w if horiz else 10, 10 if horiz else w, 14, centered=(True, True, False)).translate((x, y, TOP + IH - 13))
    return h.cut(k)
h = kerbe(h, -50, -OD/2 + WD/2, 40, True)     # Märklin-Kabel (vorne)
h = kerbe(h, 50, -OD/2 + WD/2, 30, True)      # Märklin-Kabel 2
h = kerbe(h, OW/2 - WD/2, 40, 16, False)      # Kabel zum Pult
h = kerbe(h, -OW/2 + WD/2, 0, 16, False)      # 5 V vom Netzteil
h = kerbe(h, 60, OD/2 - WD/2, 16, True)       # Häuser
h = kerbe(h, OW/2 - WD/2, -70, 16, False)     # Mühle/Qualm (8er Relais)
# Lüftungsschlitze oben in den Längswänden (senkrecht -> stützenfrei)
for i in range(8):
    x = -60 + i*17
    h = h.cut(cq.Workplane("XY").box(3, 10, 20, centered=(True, True, False)).translate((x, OD/2 - WD/2, TOP + 8)))
cq.exporters.export(h, "box-stl/box-haube.stl", tolerance=0.05)
# ---------- Montageplatte (v3: nach Tims Messung 23.11.) ----------
# Platinen MIT Löchern: Loch 4,6 in der Platte (±0,8 mm Spiel), Abstandshülse 6 mm, M3x16 von unten, Mutter oben.
# Platinen OHNE Löcher (MCP, LLC): Mulde + 2 Auflageleisten + Klemmleiste mit 2 Schrauben 3x10 (keine Clips).
pw, pd = IW - 0.6, ID - 0.6
p = cq.Workplane("XY").box(pw, pd, PL, centered=(True, True, False))
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = sx*(IW/2 - 5), sy*(ID/2 - 5)
        p = p.cut(cq.Workplane("XY").center(cx, cy).circle(1.7).extrude(PL + 1).translate((0, 0, -0.5)))
        p = p.cut(cq.Workplane("XY").center(cx, cy).circle(3.2).extrude(1.6).translate((0, 0, -0.01)))
def loecher(p, mx, my, lx, ly, ecken=((-1,-1),(1,-1),(-1,1),(1,1))):
    for sx, sy in ecken:
        x, y = mx + sx*lx/2, my + sy*ly/2
        p = p.cut(cq.Workplane("XY").center(x, y).circle(2.3).extrude(PL + 1).translate((0, 0, -0.5)))
        p = p.cut(cq.Workplane("XY").center(x, y).circle(3.3).extrude(2.0).translate((0, 0, -0.01)))   # Kopf versenkt
        p = p.cut(cq.Workplane("XY").center(x, y).circle(4.6).circle(4.0).extrude(0.6).translate((0, 0, PL - 0.6)))  # Ring: Hülse hier
    return p
R16 = (0, 64, 170.5, 73.6)          # 16er Relais: Lochabstand lang x quer (gemessen)
SH  = (-47, -73, 74.6, 46.0)        # ESP-Shield (gemessen)
A8  = (-23, -11, 136.0, 42.0)       # Adapterplatte 8er Relais (Adapter folgt, wenn das Board da ist)
p = loecher(p, *R16)
p = loecher(p, *SH)
for sx in (-1, 1):                  # 8er-Adapter: 4 Dome mit Vorbohrung (Schraube 3x12)
    for sy in (-1, 1):
        x, y = A8[0] + sx*A8[2]/2, A8[1] + sy*A8[3]/2
        p = p.union(cq.Workplane("XY").center(x, y).circle(3.5).extrude(4).translate((0, 0, PL)))
        p = p.cut(cq.Workplane("XY").center(x, y).circle(1.25).extrude(10).translate((0, 0, PL - 2)))
SPALT, WAND, LEISTE_H, PLATINE = 0.6, 1.2, 2.5, 1.6
KLEMM = []                          # (mx, my, L, B, entlang_x)  L = parallel zu den Pinreihen
def mulde(p, mx, my, L, B, ex):
    iL, iB = L + 2*SPALT, B + 2*SPALT
    hw = LEISTE_H + PLATINE - 0.3                    # Wandhöhe = Höhe der Klemm-Dome (0,3 Vorspannung)
    def R(a, b, cx=0, cy=0):                         # Rechteck in lokalen Koordinaten (a entlang L)
        return (cq.Workplane("XY").center(mx + (cx if ex else cy), my + (cy if ex else cx))
                .rect(a if ex else b, b if ex else a))
    fr = R(iL + 2*WAND, iB + 2*WAND).extrude(hw).cut(R(iL, iB).extrude(hw))
    for s in (-1, 1):                                # Auflageleisten an den Enden (pinfreie Mitte)
        fr = fr.union(R(1.6, min(8.0, B - 6), s*(L/2 - 0.8)).extrude(LEISTE_H))
        dx = s*(iL/2 + WAND + 3.5)
        fr = fr.union(R(7, 7, dx).extrude(hw))       # Dom für die Klemmleiste
        hx, hy = (mx + dx, my) if ex else (mx, my + dx)
        fr = fr.cut(cq.Workplane("XY").center(hx, hy).circle(1.25).extrude(20).translate((0, 0, -5)))
    p = p.union(fr.translate((0, 0, PL)))
    KLEMM.append((L, B, iL))
    return p
p = mulde(p, 20, -56, 26.3, 20.9, True)     # MCP (WCMCU), Pinreihen längs
p = mulde(p, 8, -91, 15.1, 15.0, False)     # LLC1, Pinreihen in y-Richtung
p = mulde(p, 30, -91, 15.1, 15.0, False)    # LLC2
FELD = [(0, 64, 182, 92, "16 Relais"), (-23, -11, 144, 52, "8er Relais - Adapter folgt"),
        (73, -11, 40, 52, "WAGO"), (-47, -73, 82, 60, "ESP32 + Shield"), (70, -78, 30, 50, "frei")]
for x, y, w, d, t in FELD:
    p = p.cut(cq.Workplane("XY").center(x, y).rect(w, d).rect(w - 1.6, d - 1.6).extrude(0.6).translate((0, 0, PL - 0.6)))
for x, y, t, sz in [(0, 64, "16 Relais", 6), (-23, -11, "8er Relais - Adapter folgt", 5), (73, -11, "WAGO", 5),
                    (-47, -73, "ESP32 + Shield", 5), (20, -39, "MCP", 4), (19, -111.5, "LLC1   LLC2", 3)]:
    p = p.cut(cq.Workplane("XY").workplane(offset=PL - 0.6).center(x, y).text(t, sz, 0.6, kind="bold"))
cq.exporters.export(p, "box-stl/box-montageplatte.stl", tolerance=0.05)
# ---------- Klemmleisten (flach drucken) ----------
for name, (L, B, iL) in zip(["mcp", "llc", "llc"], KLEMM):
    lang = iL + 2*WAND + 14
    k = cq.Workplane("XY").box(lang, 5.0, 3.0, centered=(True, True, False))
    for s in (-1, 1):
        k = k.cut(cq.Workplane("XY").center(s*(iL/2 + WAND + 3.5), 0).circle(1.7).extrude(5).translate((0, 0, -1)))
    cq.exporters.export(k, f"box-stl/klemmleiste-{name}.stl", tolerance=0.05)
# ---------- Abstandshülsen (8 Stück: 4x 16er, 4x Shield) ----------
a = cq.Workplane("XY").circle(4.0).circle(1.7).extrude(6)
cq.exporters.export(a, "box-stl/abstandshuelse-6mm.stl", tolerance=0.05)
print("Haube", OW, "x", OD, "x", IH + TOP, " Platte", pw, "x", pd, "x", PL)
# ---------- Shield-Adapter v2 (23.11.: 4 Löcher, Lochmitten aus Tims Fotos/Messung) ----------
# Lochbild rel. Loch oben links (USB/DC links), y nach oben: oben links, rechts oben, rechts unten, unten links
import math
HP = [(0, 0), (SH_DX := 60.0, -15.6), (SH_DX, -42.8), (-0.6, -46.6)]   # Tim: Reihen 60, Lochmitte 1,6+1,6 von oben, 34,2/7,0 von unten, Platine 75 x 53
OUT = (-12.0, 63.0, -49.8, 3.2)                         # Platinenumriss 75 x 53 rel. Loch oben links
BOSS = [(SH[0] + sx*SH[2]/2, SH[1] + sy*SH[3]/2) for sx in (-1, 1) for sy in (-1, 1)]
best = None
for ix in range(-200, 0):
    for iy in range(-220, -60):
        x, y = ix*0.5, iy*0.5
        x0, x1, y0, y1 = x + OUT[0], x + OUT[1], y + OUT[2], y + OUT[3]
        if x0 < -97 or x1 > -4 or y0 < -112 or y1 > -39 or (x0 < -88 and y0 < -104):
            continue
        if min(y + b for a, b in HP) < -101:
            continue
        d = min(math.dist((x + a, y + b), bb) for a, b in HP for bb in BOSS)
        if best is None or d > best[0]:
            best = (d, x, y)
_, PX, PY = best
SH_L = [(PX + a, PY + b) for a, b in HP]
xs = [p[0] for p in SH_L + BOSS]; ys = [p[1] for p in SH_L + BOSS]
ax0, ax1, ay0, ay1 = min(xs) - 7, max(xs) + 5.5, min(ys) - 7, max(ys) + 7
ad = cq.Workplane("XY").center((ax0 + ax1)/2, (ay0 + ay1)/2).rect(ax1 - ax0, ay1 - ay0).extrude(3)
for x, y in BOSS:
    ad = ad.union(cq.Workplane("XY").center(x, y).circle(4.5).extrude(13))
    ad = ad.cut(cq.Workplane("XY").center(x, y).circle(1.25).extrude(12).translate((0, 0, -0.5)))
for x, y in SH_L:
    ad = ad.union(cq.Workplane("XY").center(x, y).circle(6.0).extrude(19))
    ad = ad.cut(cq.Workplane("XY").center(x, y).circle(1.25).extrude(13).translate((0, 0, 6.5)))
cx, cy = (SH_L[0][0] + SH_L[1][0])/2, (SH_L[0][1] + SH_L[3][1])/2
for dx in (-16, 0, 16):            # Fenster gegen Materialverbrauch
    ad = ad.cut(cq.Workplane("XY").center(cx + dx, cy).rect(11, 20).extrude(5).translate((0, 0, -1)))
ad = ad.cut(cq.Workplane("XY").workplane(offset=2.4).center(cx, ay1 - 4).text("USB links", 4, 0.6, kind="bold"))
cq.exporters.export(ad, "box-stl/shield-adapter.stl", tolerance=0.05)
print("Shield-Löcher", [tuple(round(v, 1) for v in p) for p in SH_L], "Abstand Dom", round(best[0], 1), "Adapter", (ax0, ax1, ay0, ay1))
