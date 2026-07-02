"""Mixed-width panelization — brick bands with seams placed by DP to dodge the figures.

The soffit is split into 1.0 m horizontal bands (supplier short-side limit). Within each
band, panel widths are multiples of 0.5 m (0.5-2.0 m, "combinations that add up"), and a
dynamic program places every vertical seam where it crosses the fewest figure lines —
optimal per band, brick-style staggering falls out naturally. Band phase (0 / 0.5 m) is
also tried and the better kept.

Writes out/panels.json (same schema the viewer + export_panels.py read).

    uv run python panelize_mixed.py
"""
import json, math, bisect
from pathlib import Path

HERE = Path(__file__).parent; OUT = HERE / "out"
CS = 500.0                    # width module (mm)
BH = 1000.0                   # band height (mm) <= 110 cm supplier limit
WMAX = 4                      # max panel width in modules (2.0 m <= 230 cm limit)
ALPHA, BETA = 1.0, 10.0       # cost: panels vs seam-crossings (breaks dominate)

d = json.load(open(HERE / "ceiling.json")); cells = d["cells"]; tcs = d["cell_mm"]
strokes = [b["points"] for b in json.load(open(OUT / "paths.json")) if b.get("color") != "#f2f2f2"]
xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
x0, x1 = min(xs)-tcs/2, max(xs)+tcs/2; y0, y1 = min(ys)-tcs/2, max(ys)+tcs/2
NX = math.ceil((x1-x0)/CS)

def covered(a, b, c, e):
    m = tcs/2
    return any(a-m <= p[0] <= c+m and b-m <= p[1] <= e+m for p in cells)

# stroke crossings of vertical 0.5m lines (x0+k*CS) and arbitrary horizontal lines
vcross = [[] for _ in range(NX+1)]
for pts in strokes:
    for k in range(len(pts)-1):
        (ax, ay), (bx, by) = pts[k], pts[k+1]
        lo = max(0, math.ceil((min(ax,bx)-x0)/CS)); hi = min(NX, math.floor((max(ax,bx)-x0)/CS))
        for ii in range(lo, hi+1):
            X = x0+ii*CS
            if (ax-X)*(bx-X) < 0: vcross[ii].append(ay + (X-ax)/(bx-ax)*(by-ay))
for L in vcross: L.sort()

def hline_crossings(Y, xa, xb):
    out = []
    for pts in strokes:
        for k in range(len(pts)-1):
            (ax, ay), (bx, by) = pts[k], pts[k+1]
            if (ay-Y)*(by-Y) < 0:
                x = ax + (Y-ay)/(by-ay)*(bx-ax)
                if xa <= x <= xb: out.append(x)
    return out

def solve(phase):
    """phase 0 or 0.5: band edges at y0 + phase + k*BH (partial first/last bands)."""
    edges = []
    yb = y0 + (phase % BH if phase else 0)
    if yb > y0: edges.append((y0, yb))
    while yb < y1 - 1:
        edges.append((yb, min(yb+BH, y1))); yb += BH
    panels, breaks = [], []
    for (ba, bb) in edges:
        # covered runs of width-modules in this band
        run = []
        for i in range(NX):
            ok = covered(x0+i*CS, ba, x0+(i+1)*CS, bb)
            if ok: run.append(i)
            if (not ok or i == NX-1) and run:
                s, e = run[0], run[-1]+1          # cells [s,e)
                n = e - s
                # DP over seam positions: cost = ALPHA per panel + BETA per crossing at interior seams
                INF = 1e18; dp = [INF]*(n+1); dp[0] = 0.0; prev = [-1]*(n+1)
                for k in range(1, n+1):
                    for w in range(1, min(WMAX, k)+1):
                        seam = 0 if k == n else len(vcross[s+k]) and (bisect.bisect_right(vcross[s+k], bb) - bisect.bisect_left(vcross[s+k], ba))
                        c = dp[k-w] + ALPHA + BETA*seam
                        if c < dp[k]: dp[k] = c; prev[k] = k-w
                    if prev[k] < 0: dp[k] = INF   # unreachable guard (shouldn't happen)
                k = n; cuts = []
                while k > 0: cuts.append(k); k = prev[k]
                cuts = sorted(set(cuts))          # right edges of panels (in cells from s)
                a = 0
                for c in cuts:
                    panels.append([round(x0+(s+a)*CS,1), round(ba,1), round(x0+(s+c)*CS,1), round(bb,1)])
                    if c < n:                     # interior seam -> breaks
                        X = x0+(s+c)*CS
                        aa = bisect.bisect_left(vcross[s+c], ba); bbx = bisect.bisect_right(vcross[s+c], bb)
                        breaks += [[round(X,1), round(y,1)] for y in vcross[s+c][aa:bbx]]
                    a = c
                run = []
        # horizontal seam at band bottom (if a band exists below)
        if ba > y0 + 1:
            breaks += [[round(x,1), round(ba,1)] for x in hline_crossings(ba, x0, x1)]
    return panels, breaks

best = None
for phase in (0.0, 500.0):
    panels, breaks = solve(phase)
    key = (len(breaks), len(panels))
    if best is None or key < best[0]: best = (key, panels, breaks, phase)
(_, panels, breaks, phase) = best

out = {"panel_w": 2000.0, "panel_h": BH, "origin": [round(x0,1), round(y0,1)],
       "panels": panels, "vlines": [], "hlines": [], "breaks": breaks, "mixed": True, "module_mm": CS}
(OUT / "panels.json").write_text(json.dumps(out))

from collections import Counter
sizes = Counter(f"{(p[2]-p[0])/1000:.1f}x{(p[3]-p[1])/1000:.1f}" for p in panels)
print(f"band-DP layout (phase {phase/1000:.1f} m): {len(panels)} panels, {len(breaks)} seam breaks   (uniform 2x1: 68 / 98)")
for s, n in sizes.most_common():
    w, h = (float(v) for v in s.split("x"))
    print(f"  {n:3d} x {s} m  (~{w*h*6*1.45:.1f} kg)")
