"""Group the neon into per-figure dimmable channels (foundation for the touch interaction).

Each figure colour = one PWM channel (one MOSFET, ESP32 LEDC). Reports LED length, load,
current, and which panels/feeds belong to each channel. Writes out/channels.json.

    uv run python channels.py
"""
import json, math
from pathlib import Path
from collections import defaultdict

OUT = Path(__file__).parent / "out"
NAMES = {"#ff3ea5":"pink","#ffd23d":"yellow","#00e5ff":"cyan","#ff7a1a":"orange",
         "#a05bff":"purple","#39ff88":"green","#2b6bff":"blue","#f2f2f2":"rings"}
WPM = 10.0      # W/m (confirm against strip datasheet)
VOLTS = 12.0    # 12 V neon-flex
MAXRUN = 2500.0 # max continuous run per power feed at 12 V (mm) — voltage-drop limit

bodies = json.load(open(OUT / "paths.json"))
slen = lambda p: sum(math.dist(p[i], p[i+1]) for i in range(len(p)-1))

# continuous neon: feeds are set by run length / MAXRUN per body, NOT by panel seams
figpts = defaultdict(list); ch = defaultdict(lambda: {"len": 0.0, "feeds": 0})
for b in bodies:
    L = slen(b["points"]); figpts[b["color"]].append(b["points"])
    ch[b["color"]]["len"] += L
    ch[b["color"]]["feeds"] += max(1, math.ceil(L / MAXRUN))   # one continuous run per body

out = []; print(f"{'ch':3}{'colour':8}{'LED m':>7}{'W':>6}{f'A@{VOLTS:.0f}V':>7}{'feeds':>7}{'A/feed':>8}")
for i, (col, d) in enumerate(sorted(ch.items(), key=lambda x: -x[1]["len"]), 1):
    w = d["len"]/1000*WPM; a = w/VOLTS; apf = a/max(1, d["feeds"])
    print(f"{i:<3}{NAMES.get(col,col):8}{d['len']/1000:7.1f}{w:6.0f}{a:7.1f}{d['feeds']:7}{apf:8.1f}")
    out.append({"ch": i, "colour": NAMES.get(col, col), "hex": col, "led_m": round(d["len"]/1000, 1),
                "watts": round(w), "volts": VOLTS, "amps": round(a, 1), "feeds": d["feeds"],
                "amps_per_feed": round(apf, 1)})
tw = sum(c["watts"] for c in out); tf = sum(c["feeds"] for c in out)
print(f"\n{len(out)} channels · {tw} W · {tw/VOLTS:.0f} A @ {VOLTS:.0f} V · {tf} power feeds (@{MAXRUN/1000:.1f} m) -> 1 MOSFET/channel on one ESP32")
json.dump(out, open(OUT / "channels.json", "w"), indent=1)
