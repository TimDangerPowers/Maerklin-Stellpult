"""Erzeugt fensterbahn/web.h (Website im ESP) aus der Pult-Geometrie (stellpult_v7.py).
Aufruf aus diesem Ordner: python gen_web.py"""
import math
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "pult" / "stellpult_v7.py"
ns = {}
exec(SRC.read_text().split("# ---------------- Hilfen")[0], ns)
GLEISE, PIX, TASTER, PRELL = ns["GLEISE"], ns["PIX"], ns["TASTER"], ns["PRELL"]
H = 185.0
def P(x, y): return f"{x:.1f},{H - y:.1f}"
def poly(pts): return " ".join(P(float(x), float(y)) for x, y in pts)

gleise = "".join(f'<polyline class="g" points="{poly(g)}"/>' for g in GLEISE)
# Hauptrunde für den Lichtpunkt: 0 -> 3 -> 4 -> 7r -> 6r -> 5r -> 2r -> 1r
G = [[(float(x), float(y)) for x, y in g] for g in GLEISE]
runde = G[0] + G[3] + G[4] + G[7][::-1] + G[6][::-1] + G[5][::-1] + G[2][::-1] + G[1][::-1]
runde_d = "M" + " L".join(P(x, y) for x, y in runde) + " Z"

def pfeil(x, y, d):
    dx, dy = d; n = math.hypot(dx, dy); dx, dy = dx / n, dy / n; px, py = -dy, dx
    L = 3.0
    a = (x - dx * L, y - dy * L); tip = (x + dx * (L + 1.6), y + dy * (L + 1.6)); b = (x + dx * (L - 1.4), y + dy * (L - 1.4))
    pts = [a, b, (b[0] + px * 2.6, b[1] + py * 2.6), tip, (b[0] - px * 2.6, b[1] - py * 2.6), b]
    return f'M{P(*a)} L{P(*b)} M{P(*pts[2])} L{P(*tip)} L{P(*pts[4])} Z'

def blitz(x, y):
    pts = [(0.9, 4.2), (-2.4, 0), (0.2, 0), (-0.9, -4.2), (2.4, 0.5), (-0.2, 0.5)]
    return "M" + " L".join(P(x + a, y + b) for a, b in pts) + " Z"

anz = []
for n, ((x, y), f, d) in PIX.items():
    if n in ("AUTO", "LICHT", "ANIM"): continue
    if f == "pfeil": anz.append(f'<path id="L_{n}" class="pf" d="{pfeil(x, y, d)}"/>')
    elif f == "blitz": anz.append(f'<path id="L_{n}" class="bl" d="{blitz(x, y)}"/>')
    else: anz.append(f'<circle id="L_{n}" class="sig" cx="{x}" cy="{H - y}" r="3.6"/>')
anz = "".join(anz)

knoepfe = []
CMD = {"W1": "W1", "W2": "W2", "W3": "W3", "W4": "W4", "S1_G": "S1G", "S1_R": "S1R", "S2_G": "S2G", "S2_R": "S2R",
       "E": "E", "T1": "T1", "T2": "T2"}
for n, (x, y, o, k, lbl) in TASTER.items():
    if n not in CMD: continue
    cls = "kn" + (" gr" if n.endswith("_G") else " rt" if n.endswith("_R") else "")
    knoepfe.append(f'<g class="{cls}" data-c="{CMD[n]}" id="K_{n}"><circle cx="{x}" cy="{H - y}" r="7.5"/>'
                   + (f'<text x="{x}" y="{H - y + 1.5}">{n}</text>' if not n.startswith("S") else "") + "</g>")
    if lbl and n.startswith("S"):
        knoepfe.append(f'<text class="lb" x="{lbl[1]}" y="{H - lbl[2] + 1.2}">{lbl[0]}</text>')
knoepfe = "".join(knoepfe)
prell = "".join(f'<rect class="pb" x="{x - 1.3}" y="{H - y - 4.5}" width="2.6" height="9"/>' for x, y in PRELL)

HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#07090d"><title>Fensterbahn</title><style>
:root{--bg:#07090d;--pan:#10151d;--line:#243040;--txt:#e8eef6;--mut:#7d8a9a;--amb:#ffb02e;--grn:#2bf07a;--red:#ff3b3b;--blu:#4aa8ff;--vio:#b07bff}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.35 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
header{display:flex;align-items:center;gap:10px;padding:14px 16px 6px}h1{font-size:19px;margin:0;letter-spacing:.5px;font-weight:700}
h1 b{color:var(--amb)}.chip{margin-left:auto;font-size:12px;color:var(--mut);display:flex;gap:6px}.chip i{width:8px;height:8px;border-radius:50%;display:inline-block;background:#444;margin-right:3px;vertical-align:middle}
.ok i{background:var(--grn);box-shadow:0 0 6px var(--grn)}.bad i{background:var(--red);box-shadow:0 0 6px var(--red)}
#msg{margin:2px 16px 8px;padding:9px 12px;border-radius:12px;background:linear-gradient(90deg,#141b25,#0d1219);border:1px solid var(--line);font-weight:600;min-height:20px;transition:box-shadow .3s}
#msg.neu{box-shadow:0 0 0 1px var(--amb),0 0 18px #ffb02e44}
.plan{margin:0 8px;border-radius:18px;background:radial-gradient(ellipse at 50% 30%,#111a26,#090c11 75%);border:1px solid var(--line);padding:6px;position:relative;overflow:hidden}
svg{width:100%;height:auto;display:block}.g{fill:none;stroke:#2c3a4c;stroke-width:2.6;stroke-linecap:round;stroke-linejoin:round}
.glow .g{stroke:#3d5a7a;filter:url(#gl)}.pb{fill:#2c3a4c}
.pf{fill:#1a2330;stroke:#1a2330;stroke-width:1.6;stroke-linecap:round;transition:all .35s}.pf.an{fill:var(--amb);stroke:var(--amb);filter:url(#gl)}
.pf.flash{fill:var(--grn);stroke:var(--grn)}.pf.aus{fill:#3a1414;stroke:#3a1414}
.sig{fill:#3a1010;transition:all .3s}.sig.rot{fill:var(--red);filter:url(#gl)}.sig.gruen{fill:var(--grn);filter:url(#gl)}
.bl{fill:#1a2330;transition:all .3s}.bl.an{fill:var(--amb);filter:url(#gl)}
.kn{cursor:pointer}.kn circle{fill:#151c26;stroke:#33445a;stroke-width:.8;transition:all .15s}.kn text{fill:#c9d4e2;font-size:4.6px;font-weight:700;text-anchor:middle;pointer-events:none}
.kn:active circle,.kn.druck circle{fill:#24324a;stroke:var(--blu);transform-box:fill-box;transform-origin:center;transform:scale(.9)}
.kn.gr circle{stroke:#1f8a4b}.kn.rt circle{stroke:#8a2323}.lb{fill:var(--mut);font-size:4.4px;font-weight:700;text-anchor:middle}
.berg{fill:#5a6b80;font-size:5px;font-weight:700;letter-spacing:1px;text-anchor:middle}
#zug{fill:#fff;filter:url(#gl2);opacity:0;transition:opacity .6s}#zug.an{opacity:1}
.bar{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 8px}
button{font:inherit;font-weight:700;border:1px solid var(--line);background:linear-gradient(180deg,#151c27,#0e131a);color:var(--txt);border-radius:16px;padding:14px 10px;cursor:pointer;transition:all .15s;position:relative}
button:active{transform:scale(.97)}button small{display:block;font-weight:500;color:var(--mut);font-size:12px;margin-top:2px}
.on-b{border-color:var(--blu);box-shadow:0 0 0 1px var(--blu),0 0 22px #4aa8ff40}.on-a{border-color:var(--amb);box-shadow:0 0 0 1px var(--amb),0 0 22px #ffb02e40}
#bLoop{padding-right:40px}#bStop{grid-column:1/-1;background:linear-gradient(180deg,#5c0f0f,#3a0808);border-color:#a82020;font-size:18px;letter-spacing:2px}
.ring{position:absolute;right:10px;top:50%;width:26px;height:26px;margin-top:-13px}.ring circle{fill:none;stroke-width:3}
details{margin:4px 8px 30px;border:1px solid var(--line);border-radius:16px;background:var(--pan);padding:4px 14px}
summary{padding:10px 0;font-weight:700;cursor:pointer;color:var(--mut)}label{display:block;margin:10px 0 4px;color:var(--mut);font-size:13px}
input{width:100%;padding:10px;border-radius:10px;border:1px solid var(--line);background:#0b0f15;color:var(--txt);font:inherit}input[type=range]{padding:0}
.testgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin:10px 0}.testgrid button{padding:10px 6px;font-size:13px}.hinweis{color:var(--mut);font-size:13px}.hausz{display:grid;grid-template-columns:70px 1fr;gap:6px 10px;align-items:center;margin:10px 0;padding-bottom:10px;border-bottom:1px solid var(--line)}.hausz input{grid-column:1/-1}.hausz span{grid-column:1/-1;color:var(--mut);font-size:12px}.hausz select{font:inherit;background:#10151d;color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px}
.zeile{display:flex;justify-content:space-between;color:var(--mut);font-size:13px;margin:8px 0}a{color:var(--blu)}
@media(min-width:900px){body{max-width:1100px;margin:auto}.bar{grid-template-columns:repeat(4,1fr)}#bStop{grid-column:auto}}
</style></head><body>
<header><h1>Fenster<b>bahn</b></h1><div class="chip"><span id="cR"><i></i>Relais</span><span id="cP"><i></i>Pult</span></div></header>
<div id="msg">Verbinde …</div>
<div class="plan"><svg viewBox="0 0 350 185" id="sv"><defs>
<filter id="gl" filterUnits="userSpaceOnUse" x="-10" y="-10" width="370" height="205"><feGaussianBlur stdDeviation="1.4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="gl2" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g class="glow">@@GLEISE@@</g>@@PRELL@@<text class="berg" x="55" y="105">BERG</text>
<path id="runde" d="@@RUNDE@@" fill="none" stroke="none"/><circle id="zug" r="2.6"/>
@@ANZ@@@@KNOEPFE@@</svg></div>
<div class="bar">
<button id="bWechsel" data-c="AUTO1">Zugwechsel<small id="sGleis">Gleis 1 fährt ab</small></button>
<button id="bLoop" data-c="LOOP">Dauerschleife<small id="sLoop">aus</small><svg class="ring" viewBox="0 0 30 30"><circle cx="15" cy="15" r="12" stroke="#243040"/><circle id="ringv" cx="15" cy="15" r="12" stroke="#4aa8ff" stroke-dasharray="75.4" stroke-dashoffset="75.4" transform="rotate(-90 15 15)" stroke-linecap="round"/></svg></button>
<button id="bLicht" data-c="LICHT">Licht<small id="sLicht">Tag</small></button>
<button id="bAnim" data-c="ANIM">Animation<small id="sAnim">Mühle · Qualm · Schweißen</small></button>
<button id="bStop" data-c="STOP">STOP</button></div>
<details><summary>Einstellungen</summary>
<label>Dauerschleife: Zeit zwischen zwei Zugwechseln: <b id="tTakt">120</b> s</label><input type="range" id="takt" min="30" max="600" step="10" value="120">
<form method="post" action="/wlan"><label>Heim-WLAN (Name)</label><input name="ssid" autocomplete="off"><label>Passwort</label><input name="pass" type="password">
<p><button type="submit">WLAN speichern &amp; neu starten</button></p></form>
<div class="zeile"><span>Firmware <b id="fw"></b> <small id="upd"></small></span><a href="#" id="check">Jetzt nach Update suchen</a></div>
<form method="post" action="/token"><label>GitHub-Schlüssel für automatische Updates <small id="tok"></small></label><input name="token" type="password" autocomplete="off" placeholder="github_pat_...">
<p><button type="submit">Schlüssel speichern</button></p></form>
<div class="zeile"><span>Update von Hand</span><a href="/update">Datei hochladen</a></div>
<div class="zeile"><span>Display</span><span id="cO"></span></div><div class="zeile"><span>I²C-Bus</span><span id="i2c"></span></div><div class="zeile"><span>Netz</span><span id="net"></span></div></details>
<details><summary>Häuser</summary><p class="hinweis">Haus 1 ist der erste LED-Streifen an der Kette, Haus 2 der zweite usw.</p><div id="hausListe"></div></details>
<details><summary>Test</summary>
<p class="hinweis">Der Märklin-Trafo darf an bleiben: einzelne Relais klicken nur, ohne „Puls“ schaltet keine Weiche.</p>
<div class="testgrid"><button data-t="a=rel">Alle Relais nacheinander</button><button data-t="a=led">LED-Test</button><button data-t="a=pultan">Pult: alle LEDs an</button><button data-t="a=stop">Test stoppen</button></div>
<div class="testgrid" id="relTest"></div></details>
<script>
const $=id=>document.getElementById(id);let S=null,V=-1,msgAlt='';
const LICHT=['Tag','Abend','Zufall'],WL=['W1','W2','W3','W4'];
function cls(e,c,on){e&&e.classList.toggle(c,!!on)}
function zeige(s){S=s;const t=Date.now();
 WL.forEach((w,i)=>{const g=$('L_'+w+'_G'),a=$('L_'+w+'_A'),ab=s.w[i];
  if(!g)return;const vorher=g.dataset.z;g.dataset.z=ab;
  if(vorher!==undefined&&vorher!=String(ab)){const n=ab?a:g,o=ab?g:a;cls(n,'flash',1);cls(o,'aus',1);setTimeout(()=>{cls(n,'flash',0);cls(o,'aus',0)},900)}
  cls(g,'an',!ab);cls(a,'an',ab)});
 [['L_S1',s.s[0]],['L_S2',s.s[1]]].forEach(([id,gr])=>{cls($(id),'gruen',gr);cls($(id),'rot',!gr)});
 cls($('L_E'),'an',s.e);cls($('L_T1'),'an',s.t[0]);cls($('L_T2'),'an',s.t[1]);
 if(s.msg!==msgAlt){$('msg').textContent=s.msg;msgAlt=s.msg;const m=$('msg');cls(m,'neu',1);setTimeout(()=>cls(m,'neu',0),900)}
 cls($('bLoop'),'on-b',s.loop);$('sLoop').textContent=s.loop?('nächster Wechsel in '+Math.floor(s.rest/60)+':'+String(s.rest%60).padStart(2,'0')):'aus';
 $('ringv').style.strokeDashoffset=s.loop?75.4*(s.rest/s.takt):75.4;
 cls($('bWechsel'),'on-b',s.wechsel);$('sGleis').textContent='Gleis '+s.gleis+' fährt ab';
 $('sLicht').textContent=LICHT[s.licht];cls($('bLicht'),'on-a',s.licht);cls($('bAnim'),'on-a',s.anim);
 cls($('zug'),'an',s.loop||s.wechsel);
 cls($('cR'),'ok',s.rel);cls($('cR'),'bad',!s.rel);cls($('cP'),'ok',s.pult);cls($('cP'),'bad',!s.pult);
 $('fw').textContent='v'+s.fw;$('upd').textContent=s.upd?'('+s.upd+')':'';$('tok').textContent=s.tok?'(gespeichert)':'(fehlt)';$('cO').textContent=s.oled?'ok':'nicht gefunden';$('i2c').textContent=s.i2c||'';hausUI(s);$('net').textContent=s.sta?'Heim-WLAN':'eigenes WLAN „Fensterbahn“';
 if(document.activeElement!==$('takt')){$('takt').value=s.takt;$('tTakt').textContent=s.takt}}
async function hol(u){try{const r=await fetch(u,{cache:'no-store'});zeige(await r.json())}catch(e){$('msg').textContent='Keine Verbindung zur Bahn …'}}
function cmd(c){if(navigator.vibrate)navigator.vibrate(12);hol('/cmd?c='+c)}
document.querySelectorAll('[data-c]').forEach(e=>{const c=e.dataset.c;
 if(c==='E'){const an=ev=>{ev.preventDefault();cls(e,'druck',1);cmd('E')},aus=()=>{cls(e,'druck',0);cmd('E0')};
  e.addEventListener('pointerdown',an);e.addEventListener('pointerup',aus);e.addEventListener('pointerleave',()=>{if(e.classList.contains('druck'))aus()})}
 else e.addEventListener('click',()=>cmd(c))});
const HT=['Wohnhaus','Fabrik','Mühle','Bahnhof','aus'];let hausGebaut=false;
function hausUI(s){if(!s.haus)return;if(!hausGebaut){hausGebaut=true;$('hausListe').innerHTML=s.haus.map((x,i)=>`<div class="hausz"><b>Haus ${i+1}</b><select data-h="${i+1}">${HT.map((n,k)=>`<option value="${k}">${n}</option>`).join('')}</select><input type="range" min="5" max="100" step="5" data-hh="${i+1}"><span id="hp${i+1}"></span></div>`).join('');
 document.querySelectorAll('[data-h]').forEach(e=>e.onchange=()=>hol('/set?haus='+e.dataset.h+'&typ='+e.value));
 document.querySelectorAll('[data-hh]').forEach(e=>{e.oninput=()=>$('hp'+e.dataset.hh).textContent=e.value+' %';e.onchange=()=>hol('/set?haus='+e.dataset.hh+'&hell='+e.value)})}
 s.haus.forEach((x,i)=>{const sel=document.querySelector(`[data-h="${i+1}"]`),r=document.querySelector(`[data-hh="${i+1}"]`);if(document.activeElement!==sel)sel.value=x[0];if(document.activeElement!==r){r.value=x[1];$('hp'+(i+1)).textContent=x[1]+' %'}})}
const RN=['Puls','W1 gerade','W1 abzweig','W2 gerade','W2 abzweig','W3 gerade','W3 abzweig','W4 gerade','W4 abzweig','S1 rot','S1 grün','S2 rot','S2 grün','Entkuppler','Mühle','Qualm'];
RN.forEach((n,i)=>{const b=document.createElement('button');b.dataset.t='r='+(i+1);b.innerHTML=(i+1)+'<small>'+n+'</small>';$('relTest').appendChild(b)});
document.querySelectorAll('[data-t]').forEach(e=>e.addEventListener('click',()=>hol('/test?'+e.dataset.t)));
$('check').onclick=e=>{e.preventDefault();$('upd').textContent='(suche ...)';hol('/check')};
$('takt').oninput=e=>$('tTakt').textContent=e.target.value;$('takt').onchange=e=>hol('/set?takt='+e.target.value);
const R=$('runde'),Z=$('zug');let L=0,pos=0,alt=0;try{L=R.getTotalLength()}catch(e){}
function lauf(ts){if(L&&S&&(S.loop||S.wechsel)){pos=(pos+(ts-alt)*0.045)%L;const p=R.getPointAtLength(pos);Z.setAttribute('cx',p.x);Z.setAttribute('cy',p.y)}alt=ts;requestAnimationFrame(lauf)}
requestAnimationFrame(lauf);hol('/state');setInterval(()=>hol('/state'),700);
</script></body></html>"""

UPDATE = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Update</title>
<style>body{background:#07090d;color:#e8eef6;font:16px system-ui;max-width:520px;margin:40px auto;padding:0 16px}button,input{font:inherit;padding:12px;border-radius:12px;border:1px solid #243040;background:#10151d;color:#e8eef6;width:100%;margin-top:12px}</style></head>
<body><h2>Firmware-Update</h2><p>Datei <b>fensterbahn.bin</b> auswählen und hochladen. Die Bahn stoppt kurz und startet danach neu.</p>
<form method="post" enctype="multipart/form-data"><input type="file" name="f" accept=".bin"><button>Hochladen</button></form><p><a style="color:#4aa8ff" href="/">zurück</a></p></body></html>"""

html = HTML.replace("@@GLEISE@@", gleise).replace("@@PRELL@@", prell).replace("@@RUNDE@@", runde_d).replace("@@ANZ@@", anz).replace("@@KNOEPFE@@", knoepfe)
out = Path(__file__).resolve().parents[1] / "fensterbahn" / "web.h"
out.write_text('#pragma once\n// Automatisch erzeugt von gen_web.py – nicht von Hand ändern\nconst char WEB_HTML[] PROGMEM = R"HTML(' + html + ')HTML";\n'
               + 'const char UPDATE_HTML[] PROGMEM = R"HTML(' + UPDATE + ')HTML";\n')
(Path(__file__).parent / "vorschau.html").write_text(html)
print("web.h", len(html), "Bytes")
