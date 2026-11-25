/*
  Fensterbahn – Stellpult v7 Firmware
  ESP32 WROOM-32 (38 Pin) auf Shield.

  I2C (SDA 21, SCL 22, 3,3 V):
    - Pult-MCP23017 (0x20): 16 Taster KY-004 gegen GND
        A0..A7 = W1 W2 W3 W4 S1grün S1rot S2grün S2rot
        B0..B6 = E T1 T2 AUTO STOP LICHT ANIMATION   (B7 frei)
    - OLED 1,3" SH1106 (0x3C) im Pult
    - Relais-MCP23017 (Soldered, 5 V hinter LLC2, Adresse 0x21..0x27, wird gesucht)
        GPA0..GPB7 -> RELM-16 IN1..IN16 (schaltet bei LOW)
        IN1 Puls | IN2/3 W1 g/a | IN4/5 W2 | IN6/7 W3 | IN8/9 W4 | IN10/11 S1 rot/grün | IN12/13 S2 rot/grün
        IN14 Entkuppler | IN15 Mühle | IN16 Qualm   (v7.1: kein 8er-Relais, Parkgleise T1/T2 nicht geschaltet)
  GPIO 32/33 und 4 13 16 17 18 19: Reserve
  LED-Ketten (über LLC1): GPIO 14 Pult-Perlen, GPIO 2 Häuser

  Spulen: Spulen-Relais wählt die Spule, das Puls-Relais gibt nur 200 ms Braun auf die Puls-Schiene.
  Keine Spule bekommt Dauerstrom.

  AUTO: kurz drücken = ein Zugwechsel, 2 s halten = Dauerschleife (Zeit auf der Website), AUTO/STOP beendet sie.
  Website: http://bahn.local (oder IP auf dem Display). Ohne Heim-WLAN macht der ESP das WLAN "Fensterbahn" auf.
  Update: Website -> Einstellungen -> Firmware-Datei hochladen.
*/
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Update.h>
#include <Preferences.h>
#include <HTTPClient.h>
#include <HTTPUpdate.h>
#include <WiFiClientSecure.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_MCP23X17.h>
#include <U8g2lib.h>
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#ifndef AP_PASS
#define AP_PASS "fensterbahn"
#endif
#ifndef OTA_PASS
#define OTA_PASS "fensterbahn"
#endif
#include "web.h"

#define FW_VERSION "7.3"     // bei jeder neuen Version hochzählen (GitHub baut sie und der ESP holt sie sich)
#define UPDATE_URL "https://raw.githubusercontent.com/TimDangerPowers/Maerklin-Stellpult/main/firmware/"   // version.txt + fensterbahn.bin

// ================= Pins =================
const int PIN_MUEHLE = 32, PIN_QUALM = 33;
const int PIN_RESERVE[6] = {4, 13, 16, 17, 18, 19};
const int PIN_LED_PULT = 14, PIN_LED_HAUS = 2;

// Relais-Nummern am Relais-MCP (= RELM-16 IN-Nummer - 1)
enum { R_PULS = 0, R_W1G, R_W1A, R_W2G, R_W2A, R_W3G, R_W3A, R_W4G, R_W4A,
       R_S1R, R_S1G, R_S2R, R_S2G, R_E, R_MUEHLE, R_QUALM };   // v7.1: IN15/16 = Mühle/Qualm (8er-Relais entfällt)

// ================= Einstellungen =================
const uint16_t PULS_MS = 200;
const uint8_t HELL_PULT = 70, HELL_HAUS = 90;
const uint32_t GRUEN_DAUER = 8000;            // so lange bleibt das Ausfahrsignal grün
const uint32_t LANG_DRUECKEN = 2000;          // AUTO halten -> Dauerschleife
const uint32_t QUALM_MAX_MS = 5UL * 60 * 1000;
const uint32_t E_MAX_MS = 3000;
const uint32_t UMSCHALT_ANZEIGE_MS = 900;

enum HausTyp { WOHNHAUS, FABRIK, MUEHLE_HAUS, BAHNHOF };
const HausTyp HAEUSER[] = { BAHNHOF, WOHNHAUS, WOHNHAUS, FABRIK, MUEHLE_HAUS, WOHNHAUS };
const int HAUS_N = sizeof(HAEUSER) / sizeof(HAEUSER[0]);
const int LED_PRO_HAUS = 8;

// Pult-Perlen v7 (stellpult_v7.py, REIHENFOLGE). Perle 3 bleibt frei.
enum PultLed { L_AUTO, L_LICHT, L_ANIM, L_W1_G, L_W1_A, L_S2, L_S1, L_W2_G, L_W2_A,
               L_E, L_W3_G, L_W3_A, L_W4_G, L_W4_A, L_T2, L_T1, PULT_N };
const uint8_t PERLE[PULT_N] = { 0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 };
const int PERLEN_GESAMT = 30;
const uint8_t WEICHE_LED[4][2] = {{L_W1_G, L_W1_A}, {L_W2_G, L_W2_A}, {L_W3_G, L_W3_A}, {L_W4_G, L_W4_A}};

// Pult-Taster (Bit im MCP)
enum Taste { B_W1, B_W2, B_W3, B_W4, B_S1_G, B_S1_R, B_S2_G, B_S2_R, B_E, B_T1, B_T2, B_AUTO, B_STOP, B_LICHT, B_ANIM, B_FREI, TASTEN };

// ================= Zustand =================
enum Art { A_W1, A_W2, A_W3, A_W4, A_S1, A_S2 };
bool zustand[6];                 // Weiche: true = Abzweig; Signal: true = grün
uint32_t umgeschaltet[4];
bool park[2] = {true, true};
bool eAktiv = false, anim = false, qualm = false;
uint32_t eSeit = 0, animSeit = 0;
enum LichtModus { TAG, ABEND, ZUFALL } licht = TAG;
uint32_t lichtSeit = 0;
// AUTO
bool schleife = false;
uint32_t wechselMs = 120000, naechsterWechsel = 0;
uint8_t abfahrGleis = 1;         // welches Gleis fährt beim nächsten Wechsel ab (1/2)
bool wechselLaeuft = false; uint32_t wechselRot = 0; uint8_t wechselSignal = A_S1;
uint32_t autoDruck = 0; bool autoLangErledigt = false;
// Anzeige
char meldung[40] = "Bereit";
uint32_t meldungSeit = 0;
uint32_t version = 1;            // zählt bei jeder Änderung hoch (für die Website)

Adafruit_NeoPixel pult(PERLEN_GESAMT, PIN_LED_PULT, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel haus(HAUS_N * LED_PRO_HAUS, PIN_LED_HAUS, NEO_GRB + NEO_KHZ800);
Adafruit_MCP23X17 mcpPult, mcpRel;
bool pultOk = false, relOk = false, oledOk = false; uint8_t relAdr = 0;
char i2cListe[64] = "-";        // gefundene I2C-Adressen (Website)
U8G2_SH1106_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
Preferences prefs;
WebServer server(80);
bool staModus = false; String ipText = "";
String githubToken = "", updInfo = "";   // Token: nur auf der Website eintragen, nie in den Code

void melde(const char *m) { strncpy(meldung, m, sizeof(meldung) - 1); meldungSeit = millis(); version++; Serial.println(m); }

// ---------------- Relais ----------------
uint16_t relBild = 0xFFFF;       // Ausgangsbild Relais-MCP (LOW = an)
void rel(uint8_t n, bool an) {
  if (an) relBild &= ~(1u << n); else relBild |= (1u << n);
  if (relOk) mcpRel.writeGPIOAB(relBild);
}

struct Auftrag { uint8_t art; bool wert; };
Auftrag queue[24]; uint8_t qKopf = 0, qEnde = 0;
enum PulsPhase { P_FREI, P_WAHL, P_PULS, P_PAUSE } phase = P_FREI;
uint32_t phaseSeit = 0; uint8_t spule = 0;

uint8_t spuleFuer(uint8_t art, bool wert) {
  switch (art) {
    case A_W1: return wert ? R_W1A : R_W1G;
    case A_W2: return wert ? R_W2A : R_W2G;
    case A_W3: return wert ? R_W3A : R_W3G;
    case A_W4: return wert ? R_W4A : R_W4G;
    case A_S1: return wert ? R_S1G : R_S1R;
    default:   return wert ? R_S2G : R_S2R;
  }
}
void stelle(uint8_t art, bool wert, bool animiert = true) {
  if (art <= A_W4 && animiert && zustand[art] != wert) umgeschaltet[art] = millis();
  zustand[art] = wert;
  uint8_t n = (qEnde + 1) % 24;
  if (n != qKopf) { queue[qEnde] = {art, wert}; qEnde = n; }
  prefs.putBytes("z", zustand, sizeof(zustand));
  version++;
}
void pulsLoop() {
  uint32_t t = millis();
  switch (phase) {
    case P_FREI:
      if (qKopf != qEnde) { Auftrag a = queue[qKopf]; qKopf = (qKopf + 1) % 24;
        spule = spuleFuer(a.art, a.wert); rel(spule, true); phase = P_WAHL; phaseSeit = t; }
      break;
    case P_WAHL:  if (t - phaseSeit > 30)      { rel(R_PULS, true);  phase = P_PULS;  phaseSeit = t; } break;
    case P_PULS:  if (t - phaseSeit > PULS_MS) { rel(R_PULS, false); phase = P_PAUSE; phaseSeit = t; } break;
    case P_PAUSE: if (t - phaseSeit > 60)      { rel(spule, false);  phase = P_FREI; } break;
  }
}

// ---------------- Aktionen ----------------
const char *WN[4] = {"W1", "W2", "W3", "W4"};
void weiche(int w, bool abz) {
  stelle(w, abz);
  char m[40]; snprintf(m, sizeof m, "Weiche %s: %s", WN[w], abz ? "abzweig" : "gerade"); melde(m);
}
void signal(uint8_t sig, bool gruen) {
  if (gruen) {   // Fahrstraße: anderes Signal rot, Ausfahrweiche W1 passend
    uint8_t anderes = (sig == A_S1) ? A_S2 : A_S1;
    if (zustand[anderes]) stelle(anderes, false);
    bool w1 = (sig == A_S2);
    if (zustand[A_W1] != w1) stelle(A_W1, w1);
  }
  stelle(sig, gruen);
  char m[40]; snprintf(m, sizeof m, "Signal %s: %s", sig == A_S1 ? "S1" : "S2", gruen ? "Fahrt" : "Halt"); melde(m);
}
void setzePark(int i, bool an, bool melden = true) {
  park[i] = an;   // v7.1: Parkgleise nicht geschaltet, nur Anzeige prefs.putBytes("p", park, sizeof(park)); version++;
  if (melden) { char m[40]; snprintf(m, sizeof m, "Parkgleis T%d: %s", i + 1, an ? "Strom an" : "Strom aus"); melde(m); }
}
void entkuppeln(bool an) {
  if (an == eAktiv) return;
  eAktiv = an; eSeit = millis(); rel(R_E, an); version++;
  if (an) melde("Entkuppeln");
}
void setzeAnim(bool an) {
  anim = an; qualm = an; animSeit = millis();
  rel(R_MUEHLE, an); rel(R_QUALM, an); version++;
  melde(an ? "Animation läuft" : "Animation aus");
}
void naechstesLicht() {
  licht = (LichtModus)((licht + 1) % 3); lichtSeit = millis(); version++;
  const char *n[3] = {"Licht: Tag", "Licht: Abend", "Licht: Zufall"}; melde(n[licht]);
}

// Zugwechsel: der wartende Zug fährt aus, der zurückkommende hält auf demselben Gleis wieder
void zugwechsel() {
  if (wechselLaeuft) return;
  uint8_t g = abfahrGleis;
  stelle(A_W2, g == 2);                       // Einfahrt: zurück auf das Gleis, das frei wird
  signal(g == 1 ? A_S1 : A_S2, true);         // stellt W1 und das andere Signal mit
  wechselSignal = g == 1 ? A_S1 : A_S2;
  wechselLaeuft = true; wechselRot = millis() + GRUEN_DAUER;
  abfahrGleis = g == 1 ? 2 : 1;
  char m[40]; snprintf(m, sizeof m, "Zug fährt ab: Gleis %d", g); melde(m);
}
void schleifeAn(bool an) {
  schleife = an; version++;
  if (an) { zugwechsel(); naechsterWechsel = millis() + wechselMs; melde("AUTO: Dauerschleife"); }
  else melde("AUTO: aus");
}
void stopp() {
  schleife = false; wechselLaeuft = false;
  stelle(A_S1, false); stelle(A_S2, false);
  if (anim) setzeAnim(false);
  entkuppeln(false);
  melde("STOP: alle Signale Halt");
}
void autoLoop() {
  uint32_t t = millis();
  if (wechselLaeuft && (int32_t)(t - wechselRot) >= 0) {
    wechselLaeuft = false; stelle(wechselSignal, false);
    melde(wechselSignal == A_S1 ? "Signal S1: Halt" : "Signal S2: Halt");
  }
  if (schleife && (int32_t)(t - naechsterWechsel) >= 0) { zugwechsel(); naechsterWechsel = t + wechselMs; }
  if (eAktiv && t - eSeit > E_MAX_MS) entkuppeln(false);
  if (qualm && t - animSeit > QUALM_MAX_MS) { qualm = false; rel(R_QUALM, false); melde("Qualm aus (5 min)"); }
}

// Befehle (Pult und Website)
void befehl(const String &c) {
  if (c == "W1" || c == "W2" || c == "W3" || c == "W4") { int w = c[1] - '1'; weiche(w, !zustand[w]); }
  else if (c == "S1G") signal(A_S1, true);
  else if (c == "S1R") signal(A_S1, false);
  else if (c == "S2G") signal(A_S2, true);
  else if (c == "S2R") signal(A_S2, false);
  else if (c == "T1") setzePark(0, !park[0]);
  else if (c == "T2") setzePark(1, !park[1]);
  else if (c == "E") entkuppeln(true);
  else if (c == "E0") entkuppeln(false);
  else if (c == "AUTO1") { if (schleife) schleifeAn(false); else zugwechsel(); }
  else if (c == "LOOP") schleifeAn(!schleife);
  else if (c == "STOP") stopp();
  else if (c == "LICHT") naechstesLicht();
  else if (c == "ANIM") setzeAnim(!anim);
}

// ---------------- Pult-Taster ----------------
bool tAlt[TASTEN]; uint32_t tZeit[TASTEN];
void tastenLoop() {
  if (!pultOk) return;
  uint32_t t = millis();
  uint16_t alle = mcpPult.readGPIOAB();
  for (int b = 0; b < TASTEN; b++) {
    bool an = !(alle & (1u << b));
    if (an != tAlt[b] && t - tZeit[b] > 40) {
      tAlt[b] = an; tZeit[b] = t;
      switch (b) {
        case B_E: entkuppeln(an); break;
        case B_AUTO:
          if (an) { autoDruck = t; autoLangErledigt = false; }
          else if (!autoLangErledigt) befehl("AUTO1");
          break;
        default: {
          if (!an) break;
          static const char *c[TASTEN] = {"W1", "W2", "W3", "W4", "S1G", "S1R", "S2G", "S2R", "", "T1", "T2", "", "STOP", "LICHT", "ANIM", ""};
          if (c[b][0]) befehl(c[b]);
        }
      }
    }
  }
  if (tAlt[B_AUTO] && !autoLangErledigt && t - autoDruck > LANG_DRUECKEN) { autoLangErledigt = true; schleifeAn(true); }
}

// ---------------- Pult-LEDs ----------------
void setP(int led, uint32_t f) { pult.setPixelColor(PERLE[led], f); }
uint32_t pf(uint8_t r, uint8_t g, uint8_t b) { return pult.Color(r * HELL_PULT / 255, g * HELL_PULT / 255, b * HELL_PULT / 255); }
void zeichnePult() {
  uint32_t t = millis();
  const uint32_t GELB = pf(255, 170, 40), GELB_LEICHT = pf(90, 60, 12), GRUEN = pf(0, 255, 40), ROT = pf(255, 0, 0);
  for (int w = 0; w < 4; w++) {
    int g = WEICHE_LED[w][0], a = WEICHE_LED[w][1]; bool abz = zustand[w];
    if (umgeschaltet[w] && t - umgeschaltet[w] < UMSCHALT_ANZEIGE_MS) { setP(abz ? a : g, GRUEN); setP(abz ? g : a, ROT); }
    else { setP(abz ? a : g, GELB_LEICHT); setP(abz ? g : a, 0); }
  }
  setP(L_S1, zustand[A_S1] ? GRUEN : ROT);
  setP(L_S2, zustand[A_S2] ? GRUEN : ROT);
  setP(L_E, eAktiv ? GELB : 0);
  setP(L_T1, park[0] ? GELB_LEICHT : 0);
  setP(L_T2, park[1] ? GELB_LEICHT : 0);
  uint32_t blau = pf(40, 120, 255), blauDunkel = pf(10, 30, 70);
  setP(L_AUTO, schleife ? ((t / 600) % 2 ? blau : blauDunkel) : (wechselLaeuft ? blau : 0));
  const uint32_t lf[3] = {pf(120, 120, 120), pf(255, 120, 20), pf(160, 60, 255)};
  setP(L_LICHT, lf[licht]);
  setP(L_ANIM, anim ? ((t / 300) % 2 ? GELB : pf(120, 60, 10)) : 0);
  pult.show();
}

// ---------------- Häuser ----------------
struct Raum { bool an; uint32_t naechst; uint8_t effekt; };
Raum raum[HAUS_N][2];
uint32_t hf(uint8_t r, uint8_t g, uint8_t b) { return haus.Color(r * HELL_HAUS / 255, g * HELL_HAUS / 255, b * HELL_HAUS / 255); }
void setRaum(int h, int r, uint32_t f) { for (int i = 0; i < 4; i++) haus.setPixelColor(h * LED_PRO_HAUS + r * 4 + i, f); }
uint32_t schweissen(uint32_t t, int h) {
  uint32_t z = (t / 50 + h * 37) % 120;
  if (z < 40 && random(100) < 45) return hf(170, 200, 255);
  if (z < 50) return hf(90, 30, 0);
  return 0;
}
void zeichneHaeuser() {
  uint32_t t = millis();
  for (int h = 0; h < HAUS_N; h++) {
    for (int r = 0; r < 2; r++) {
      Raum &x = raum[h][r];
      if (licht == TAG) x.an = false;
      else if (licht == ABEND) { if (!x.an && t - lichtSeit > (uint32_t)(h * 2 + r) * 1500) x.an = true; }
      else if ((int32_t)(t - x.naechst) >= 0) {
        x.an = random(100) < 60;
        x.effekt = (r == 0 && random(100) < 25) ? 1 : (random(100) < 20 ? 2 : 0);
        x.naechst = t + random(8000, 45000);
      }
      uint32_t f = 0;
      if (x.an) {
        switch (HAEUSER[h]) {
          case FABRIK:  f = hf(255, 230, 190); break;
          case BAHNHOF: f = hf(255, 190, 110); break;
          default:
            if (x.effekt == 1) { uint8_t v = 60 + random(60); f = hf(v / 2, v / 2 + 10, v + 40); }
            else if (x.effekt == 2) { uint8_t v = 140 + random(70); f = hf(v, v / 3, 0); }
            else f = hf(255, 150, 60);
        }
      }
      setRaum(h, r, f);
    }
    if (HAEUSER[h] == FABRIK && anim) {      // Schweißlicht gehört zur Animation
      uint32_t s = schweissen(t, h);
      if (s) { haus.setPixelColor(h * LED_PRO_HAUS, s); haus.setPixelColor(h * LED_PRO_HAUS + 1, s); }
    }
  }
  haus.show();
}

// ---------------- Display ----------------
void zeichneDisplay() {
  if (!oledOk) return;
  uint32_t t = millis();
  oled.clearBuffer();
  oled.setFont(u8g2_font_6x12_tf);
  oled.drawUTF8(0, 10, "Fensterbahn");
  oled.drawUTF8(128 - oled.getUTF8Width(ipText.c_str()), 10, ipText.c_str());
  oled.drawHLine(0, 13, 128);
  oled.setFont(u8g2_font_7x14B_tf);
  oled.drawUTF8(0, 30, meldung);
  oled.setFont(u8g2_font_6x12_tf);
  char z[40];
  if (schleife) { uint32_t rest = (naechsterWechsel > t) ? (naechsterWechsel - t) / 1000 : 0;
    snprintf(z, sizeof z, "AUTO: Wechsel in %lu:%02lu", (unsigned long)(rest / 60), (unsigned long)(rest % 60)); }
  else snprintf(z, sizeof z, "AUTO aus  | Abfahrt: Gl.%d", abfahrGleis);
  oled.drawUTF8(0, 46, z);
  const char *ln[3] = {"Tag", "Abend", "Zufall"};
  snprintf(z, sizeof z, "Licht %s%s", ln[licht], anim ? " | Animation" : "");
  oled.drawUTF8(0, 60, z);
  if (!relOk) { oled.setDrawColor(1); oled.drawBox(0, 50, 128, 14); oled.setDrawColor(0); oled.drawUTF8(2, 61, "Relais-MCP fehlt!"); oled.setDrawColor(1); }
  oled.sendBuffer();
}

// ---------------- Website ----------------
String zustandJson() {
  uint32_t t = millis();
  uint32_t rest = (schleife && naechsterWechsel > t) ? (naechsterWechsel - t) / 1000 : 0;
  char b[700];
  snprintf(b, sizeof b,
    "{\"v\":%lu,\"w\":[%d,%d,%d,%d],\"s\":[%d,%d],\"t\":[%d,%d],\"e\":%d,\"loop\":%d,\"wechsel\":%d,\"rest\":%lu,\"takt\":%lu,"
    "\"gleis\":%d,\"licht\":%d,\"anim\":%d,\"msg\":\"%s\",\"rel\":%d,\"pult\":%d,\"oled\":%d,\"fw\":\"%s\",\"sta\":%d,\"tok\":%d,\"upd\":\"%s\",\"i2c\":\"%s\"}",
    (unsigned long)version, zustand[0], zustand[1], zustand[2], zustand[3], zustand[A_S1], zustand[A_S2], park[0], park[1], eAktiv,
    schleife, wechselLaeuft, (unsigned long)rest, (unsigned long)(wechselMs / 1000), abfahrGleis, licht, anim, meldung,
    relOk, pultOk, oledOk, FW_VERSION, staModus, githubToken.length() > 0, updInfo.c_str(), i2cListe);
  return String(b);
}
// ---------------- Update von GitHub ----------------
int versionsZahl(const String &v) {            // "7.2" -> 702
  int p = v.indexOf('.');
  return p < 0 ? v.toInt() * 100 : v.substring(0, p).toInt() * 100 + v.substring(p + 1).toInt();
}
void updatePruefen() {
  if (!staModus) { updInfo = "kein Heim-WLAN"; return; }
  WiFiClientSecure client; client.setInsecure();
  HTTPClient http; http.setTimeout(5000);
  if (!http.begin(client, String(UPDATE_URL) + "version.txt?t=" + String(millis()))) { updInfo = "GitHub nicht erreichbar"; return; }
  if (githubToken.length()) http.addHeader("Authorization", "token " + githubToken);
  int code = http.GET();
  String neu = code == 200 ? http.getString() : String("");
  neu.trim(); http.end();
  Serial.printf("Update: GitHub %s, eigene %s (HTTP %d)\n", neu.c_str(), FW_VERSION, code);
  if (code != 200) { updInfo = "GitHub-Fehler " + String(code) + (githubToken.length() ? "" : " (Token fehlt?)"); return; }
  if (versionsZahl(neu) <= versionsZahl(FW_VERSION)) { updInfo = "aktuell"; return; }
  updInfo = "lade v" + neu + " ..."; melde("Update wird geladen");
  if (oledOk) { oled.clearBuffer(); oled.setFont(u8g2_font_7x14B_tf); oled.drawUTF8(0, 30, "Update"); oled.drawUTF8(0, 50, ("v" + neu).c_str()); oled.sendBuffer(); }
  stopp();
  httpUpdate.rebootOnUpdate(true);
  if (githubToken.length()) httpUpdate.setAuthorization("token " + githubToken);
  t_httpUpdate_return r = httpUpdate.update(client, String(UPDATE_URL) + "fensterbahn.bin?v=" + neu);
  if (r == HTTP_UPDATE_FAILED) { updInfo = "Update fehlgeschlagen: " + httpUpdate.getLastErrorString(); melde("Update fehlgeschlagen"); }
}

bool otaErlaubt() {
  if (server.authenticate("bahn", OTA_PASS)) return true;
  server.requestAuthentication(); return false;
}
void webSetup() {
  server.on("/", [] { server.sendHeader("Cache-Control", "no-cache"); server.send_P(200, "text/html; charset=utf-8", WEB_HTML); });
  server.on("/state", [] { server.send(200, "application/json", zustandJson()); });
  server.on("/cmd", [] { befehl(server.arg("c")); server.send(200, "application/json", zustandJson()); });
  server.on("/set", [] {
    if (server.hasArg("takt")) { long s = server.arg("takt").toInt(); if (s >= 20 && s <= 1800) { wechselMs = s * 1000UL; prefs.putULong("takt", wechselMs);
      if (schleife) naechsterWechsel = millis() + wechselMs; version++; } }
    server.send(200, "application/json", zustandJson());
  });
  server.on("/wlan", HTTP_POST, [] {
    prefs.putString("ssid", server.arg("ssid")); prefs.putString("pass", server.arg("pass"));
    server.send(200, "text/plain; charset=utf-8", "Gespeichert. Die Bahn startet neu und wählt sich ins WLAN ein.");
    delay(500); ESP.restart();
  });
  server.on("/token", HTTP_POST, [] {
    String t = server.arg("token"); t.trim();
    githubToken = (t == "-") ? String("") : t; prefs.putString("token", githubToken);
    server.sendHeader("Location", "/"); server.send(303);
    updatePruefen(); version++;
  });
  server.on("/check", [] { updatePruefen(); version++; server.send(200, "application/json", zustandJson()); });
  server.on("/update", HTTP_GET, [] { if (!otaErlaubt()) return; server.send_P(200, "text/html; charset=utf-8", UPDATE_HTML); });
  server.on("/update", HTTP_POST, [] {
    if (!otaErlaubt()) return;
    server.send(200, "text/plain; charset=utf-8", Update.hasError() ? "Update fehlgeschlagen" : "Update ok, Neustart ...");
    delay(500); ESP.restart();
  }, [] {
    if (!server.authenticate("bahn", OTA_PASS)) return;
    HTTPUpload &u = server.upload();
    if (u.status == UPLOAD_FILE_START) { stopp(); Update.begin(UPDATE_SIZE_UNKNOWN); }
    else if (u.status == UPLOAD_FILE_WRITE) Update.write(u.buf, u.currentSize);
    else if (u.status == UPLOAD_FILE_END) Update.end(true);
  });
  server.onNotFound([] { server.sendHeader("Location", "/"); server.send(302); });
  server.begin();
}
void wlanSetup() {
  String ssid = prefs.getString("ssid", ""), pass = prefs.getString("pass", "");
#ifdef WLAN_SSID
  if (ssid == "") { ssid = WLAN_SSID; pass = WLAN_PASS; }
#endif
  WiFi.setHostname("bahn");
  if (ssid != "") {
    WiFi.mode(WIFI_STA); WiFi.begin(ssid.c_str(), pass.c_str());
    for (int i = 0; i < 60 && WiFi.status() != WL_CONNECTED; i++) delay(250);
  }
  if (WiFi.status() == WL_CONNECTED) { staModus = true; ipText = WiFi.localIP().toString(); }
  else { WiFi.mode(WIFI_AP); WiFi.softAP("Fensterbahn", AP_PASS); ipText = WiFi.softAPIP().toString(); }
  MDNS.begin("bahn"); MDNS.addService("http", "tcp", 80);
}

// ---------------- I2C-Geräte ----------------
bool da(uint8_t a) { Wire.beginTransmission(a); return Wire.endTransmission() == 0; }
void i2cScan() {                               // alle Adressen auf dem Bus, für die Website
  i2cListe[0] = 0;
  for (uint8_t a = 0x08; a < 0x78; a++) if (da(a)) { char t[6]; snprintf(t, sizeof t, "0x%02X ", a); strncat(i2cListe, t, sizeof i2cListe - strlen(i2cListe) - 1); }
  if (!i2cListe[0]) strcpy(i2cListe, "nichts gefunden");
}
void i2cGeraete() {                            // fehlende Geräte (nach)suchen – auch nachträglich eingesteckte
  if (!pultOk) { pultOk = da(0x20) && mcpPult.begin_I2C(0x20); if (pultOk) for (int i = 0; i < 16; i++) mcpPult.pinMode(i, INPUT_PULLUP); }
  if (!relOk) {
    for (uint8_t a = 0x21; a <= 0x27 && !relOk; a++) if (da(a) && mcpRel.begin_I2C(a)) { relOk = true; relAdr = a; }
    if (relOk) { mcpRel.writeGPIOAB(0xFFFF); for (int i = 0; i < 16; i++) mcpRel.pinMode(i, OUTPUT); mcpRel.writeGPIOAB(relBild); melde("Relais-MCP gefunden"); }
  }
  if (!oledOk) { oledOk = da(0x3C) && oled.begin(); if (oledOk) oled.enableUTF8Print(); }
  i2cScan();
}
void i2cSetup() {
  Wire.begin(21, 22); Wire.setClock(100000); Wire.setTimeOut(5);   // kurzer Timeout: ein hängender Bus blockiert nicht
  i2cGeraete();
  Serial.printf("I2C: %s | Pult-MCP %s, Relais-MCP %s (0x%02X), OLED %s\n", i2cListe, pultOk ? "ok" : "fehlt", relOk ? "ok" : "fehlt", relAdr, oledOk ? "ok" : "fehlt");
}

void setup() {
  Serial.begin(115200);
  for (int p : {PIN_MUEHLE, PIN_QUALM}) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  for (int p : PIN_RESERVE) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  pult.begin(); pult.clear(); pult.show();
  haus.begin(); haus.clear(); haus.show();
  randomSeed(esp_random());
  i2cSetup();
  prefs.begin("bahn", false);
  prefs.getBytes("z", zustand, sizeof(zustand));
  prefs.getBytes("p", park, sizeof(park));
  wechselMs = prefs.getULong("takt", 120000);
  githubToken = prefs.getString("token", "");
  zustand[A_S1] = zustand[A_S2] = false;                       // nach dem Einschalten alle Signale Halt
  for (int a = 0; a < 6; a++) stelle(a, zustand[a], false);   // gespeicherten Stand einmal pulsen
  setzePark(0, park[0], false); setzePark(1, park[1], false);
  if (oledOk) { oled.clearBuffer(); oled.setFont(u8g2_font_7x14B_tf); oled.drawUTF8(0, 30, "Fensterbahn"); oled.drawUTF8(0, 50, "WLAN ..."); oled.sendBuffer(); }
  wlanSetup();
  webSetup();
  updatePruefen();                                            // beim Einschalten nach neuer Firmware auf GitHub schauen
  melde(relOk ? "Bereit" : "Relais-MCP fehlt");
}

uint32_t letztesBild = 0, letztesDisplay = 0, letzterScan = 0;
void loop() {
  server.handleClient();
  tastenLoop();
  autoLoop();
  pulsLoop();
  uint32_t t = millis();
  if (t - letztesBild > 33) { letztesBild = t; zeichnePult(); zeichneHaeuser(); }
  if (t - letztesDisplay > 250) { letztesDisplay = t; zeichneDisplay(); }
  if (t - letzterScan > 5000 && (!relOk || !pultOk || !oledOk)) { letzterScan = t; i2cGeraete(); }   // alle 5 s: fehlt etwas? Bus neu ansehen
}
