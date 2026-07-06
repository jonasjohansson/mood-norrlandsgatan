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
WPM = 10.0   # W/m (confirm against strip datasheet)

bodies = json.load(open(OUT / "paths.json"))
pj = json.load(open(OUT / "panels.json")); P = pj["panels"]; breaks = pj["breaks"]
slen = lambda p: sum(math.dist(p[i], p[i+1]) for i in range(len(p)-1))

figpts = defaultdict(list); ch = defaultdict(lambda: {"len": 0.0, "panels": set(), "feeds": 0})
for b in bodies:
    figpts[b["color"]].append(b["points"]); ch[b["color"]]["len"] += slen(b["points"])
for pi, (a, b, c, e) in enumerate(P):
    for col, pts in figpts.items():
        if any(a <= x <= c and b <= y <= e for pl in pts for x, y in pl): ch[col]["panels"].add(pi)
for bp in breaks:
    for col, pts in figpts.items():
        if any(abs(bp[0]-x) < 2 and abs(bp[1]-y) < 2 for pl in pts for x, y in pl): ch[col]["feeds"] += 1

out = []; print(f"{'ch':3}{'colour':8}{'LED m':>7}{'W':>6}{'A@24V':>7}{'panels':>8}{'feeds':>7}")
for i, (col, d) in enumerate(sorted(ch.items(), key=lambda x: -x[1]["len"]), 1):
    w = d["len"]/1000*WPM
    print(f"{i:<3}{NAMES.get(col,col):8}{d['len']/1000:7.1f}{w:6.0f}{w/24:7.1f}{len(d['panels']):8}{d['feeds']:7}")
    out.append({"ch": i, "colour": NAMES.get(col, col), "hex": col, "led_m": round(d["len"]/1000, 1),
                "watts": round(w), "amps": round(w/24, 1), "panels": sorted(d["panels"]), "feeds": d["feeds"]})
tw = sum(c["watts"] for c in out)
print(f"\n{len(out)} channels, {tw} W ({tw/24:.0f} A @ 24V) -> 1 MOSFET/channel on one ESP32")
json.dump(out, open(OUT / "channels.json", "w"), indent=1)
