# Interaction — touch the pillars, the figures come alive

## Concept
A conductive **hand-sign plate** on each of the 2 entrance pillars. Place a hand on it →
the neon figures animate (a light wave/ripple washing out from that pillar across the
bodies, figures breathing/pulsing). Non-addressable coloured neon, animated by
**per-figure brightness (PWM)** — colours stay fixed, motion is in the dimming.

## Sensor — force sensing (hand rests with slight pressure)
Requirements: detect a hand *placed/resting*, **works with gloves**, bulletproof, IP-rated,
lasts years outdoors. -> **load cell / strain gauge behind the aluminium plate**
(HX711 amp -> ESP32), or an industrial piezo force switch for simple on/off.
- Gloves: irrelevant (mechanical force, not capacitance/optics).
- Weatherproof/vandal-proof: sensor fully sealed behind the solid plate; nothing exposed;
  millions of cycles.
- Continuous force -> detects presence *while held*; press hard = optional intensity map.
- Firmware auto-tracks baseline (zeroes plate weight + thermal drift), fires on threshold.
- NOT a no-contact hover (that needs optical/ToF, whose window fouls over years).

## Electrical topology
    pillar plate ─ load cell ─ HX711 ─ sensor ESP32 (at pillar) ─ ESP-NOW ─┐
                                                                           ▼
    24 V PSU(s) ──▶ 8-ch MOSFET board (main ESP32, LEDC PWM) ──▶ figure channels
                         ▲ per-figure feeds converge here (see channels.json)

- Put the sensor node **at the pillar** (short load-cell lead); send touch events to the
  ceiling controller over **ESP-NOW** (no data cable up the pillar).
- Main ESP32 in the plenum drives one logic-level MOSFET per channel (size ~10 A each).

## Channels (see `channels.py` / `out/channels.json`)
8 channels (7 figures + rings), ~1122 W / 47 A @ 24 V. Biggest: blue 8.2 A.

## Added BOM (interaction only)
- 1x main ESP32 + 8-ch logic-level MOSFET board (or 8 discrete IRLZ44N-class FETs + gate R)
- 2x pillar sensor node: ESP32 (or ESP8266) + HX711 + load cell/strain gauge
- 2x aluminium hand-sign plate + isolating standoffs + flexure/mount for the load cell
- IP67 enclosures, glands, a bit more DC cable to converge feeds at the MOSFET board

## Open items
- Confirm strip **W/m** from datasheet (tightens W/A above).
- Choose load cell range (a light hand press is ~1-5 kg-equivalent on the plate).
- Animation design: ripple-from-pillar, all-breathe, per-figure chase (all doable in PWM).
