"""Close each figure into one continuous outline; drop interior details.

Per figure (colour group): strokes shorter than MIN_KEEP mm (mouths, ears, marks) are
dropped; the remaining fragments are greedily chained end-to-end (closest endpoints
first, reversing as needed) into ONE loop, which is then closed. Pillar rings pass
through untouched. Reports every bridge it adds so odd joins are visible.

Rewrites out/paths.json (previous kept at out/paths_fragmented.json).

    uv run python outline_close.py
"""
import json, math, itertools
from pathlib import Path
from collections import defaultdict

OUT = Path(__file__).parent / "out"
MIN_KEEP = 200.0       # drop details shorter than this (mouths, marks, interior bits)
MAX_BRIDGE = 500.0     # bridge gaps up to this (continuous outline); leave bigger jumps alone

def merge_close(frags):
    """merge fragments whose endpoints are within MAX_BRIDGE (close small gaps), then close
    each resulting chain into a loop if its own ends are within MAX_BRIDGE. Returns list of
    continuous strokes (usually one closed outline; separate limbs stay separate)."""
    frags = [[list(p) for p in f] for f in frags]
    bridged = []
    while True:
        best = None
        for i in range(len(frags)):
            for j in range(i+1, len(frags)):
                for ei in (0, 1):
                    for ej in (0, 1):
                        pi = frags[i][-1 if ei else 0]; pj = frags[j][-1 if ej else 0]
                        g = math.dist(pi, pj)
                        if best is None or g < best[0]: best = (g, i, j, ei, ej)
        if best is None or best[0] > MAX_BRIDGE: break
        g, i, j, ei, ej = best
        A = frags[i] if ei else frags[i][::-1]              # A ends at the join
        B = frags[j] if not ej else frags[j][::-1]          # B starts at the join
        frags = [f for k, f in enumerate(frags) if k not in (i, j)] + [A + B]
        if g > 1: bridged.append(g)
    out = []
    for f in frags:
        if len(f) > 2 and math.dist(f[0], f[-1]) <= MAX_BRIDGE:
            if math.dist(f[0], f[-1]) > 1: bridged.append(math.dist(f[0], f[-1]))
            f = f + [f[0]]                                   # close the loop
        out.append(f)
    return out, bridged

bodies = json.load(open(OUT / "paths.json"))
(OUT / "paths_fragmented.json").write_text(json.dumps(bodies, indent=1))

figs = defaultdict(list); rings = []
for b in bodies:
    (rings if b.get("color") == "#f2f2f2" else figs[b["color"]]).append(b)

def slen(p): return sum(math.dist(p[i], p[i+1]) for i in range(len(p)-1))

out = list(rings)
for col, bs in figs.items():
    frags, dropped = [], 0
    for b in bs:
        if slen(b["points"]) < MIN_KEEP: dropped += 1
        else: frags.append([list(p) for p in b["points"]])
    loops, gaps = merge_close(frags)
    name = next(b["name"] for b in bs)
    for k, loop in enumerate(loops):
        out.append({"name": f"{name}_{k}" if len(loops) > 1 else name, "kind": "spline",
                    "points": [[round(x,1), round(y,1)] for x, y in loop], "color": col})
    closed = sum(1 for l in loops if l[0] == l[-1])
    br = ", ".join(f"{g:.0f}" for g in sorted(gaps, reverse=True))
    print(f"{col}: {len(bs)} strokes -> {len(loops)} outline(s), {closed} closed  dropped {dropped} details  bridges [{br}]")

(OUT / "paths.json").write_text(json.dumps(out, indent=1))
print(f"\nwrote out/paths.json: {len(out)} bodies ({len(rings)} rings + {len(figs)} closed figures)")
