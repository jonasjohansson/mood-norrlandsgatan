"""Bend-radius check for an LED-flex figure.

Reads an SVG of a body outline, samples every path, computes the local radius of
curvature, and flags everything tighter than the flex's minimum bend radius. Tells
you the smallest real size at which the figure is actually bendable, the total LED
run length, and writes:
  out/check_<name>.svg   overlay: green = OK, red = too tight to bend
  out/<name>.paths.json  sampled points (mm, canopy coords) for figure.py / shaper.py

    cd cad && uv run --with svgpathtools python svgcheck.py "/path/Asset 1.svg" [target_width_mm]

target_width_mm = how wide you want this body on the ceiling (default 2500).
"""
import sys, json, math
from pathlib import Path
from svgpathtools import svg2paths

MIN_BEND_MM = 150.0   # LED-flex minimum bend radius (confirm for FN-ESJT-B1023)

src = Path(sys.argv[1])
target_w = float(sys.argv[2]) if len(sys.argv) > 2 else 2500.0
name = src.stem.replace(" ", "_")
OUT = Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)

paths, _attrs = svg2paths(str(src))

# sample each path at ~1.2 svg-unit arc-length spacing
def sample(path, step=1.2):
    L = path.length()
    n = max(3, int(L / step))
    pts = []
    for i in range(n + 1):
        z = path.point(path.ilength(min(L, i / n * L)))
        pts.append((z.real, z.imag))
    return pts

def circumradius(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    A = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) / 2
    if A < 1e-9:
        return math.inf
    la = math.dist(b, c); lb = math.dist(a, c); lc = math.dist(a, b)
    return (la * lb * lc) / (4 * A)

# overall bbox (svg units)
xs, ys = [], []
for p in paths:
    b = p.bbox(); xs += [b[0], b[1]]; ys += [b[2], b[3]]
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
bw, bh = maxx - minx, maxy - miny
scale = target_w / bw                      # svg unit -> mm
thr_svg = MIN_BEND_MM / scale              # tight threshold in svg units

sampled, min_R_svg, min_at = [], math.inf, None
for p in paths:
    pts = sample(p)
    radii = [math.inf]
    for i in range(1, len(pts) - 1):
        R = circumradius(pts[i - 1], pts[i], pts[i + 1])
        radii.append(R)
        if R < min_R_svg:
            min_R_svg, min_at = R, pts[i]
    radii.append(math.inf)
    sampled.append((pts, radii))

tight = sum(1 for _, rs in sampled for r in rs if r < thr_svg)
total = sum(len(rs) for _, rs in sampled)
min_R_mm = min_R_svg * scale
feasible_w_mm = bw * (MIN_BEND_MM / min_R_svg)   # width where tightest bend == MIN_BEND

print(f"figure: {src.name}   paths: {len(paths)}")
print(f"svg bbox: {bw:.0f} x {bh:.0f} units")
print(f"at target width {target_w:.0f} mm  ->  {target_w:.0f} x {bh*scale:.0f} mm")
print(f"total LED run: {sum(p.length() for p in paths)*scale/1000:.1f} m")
print(f"tightest bend radius: {min_R_mm:.0f} mm   (need >= {MIN_BEND_MM:.0f} mm)")
print(f"points too tight to bend: {tight}/{total}")
print(f">>> to keep ALL bends >= {MIN_BEND_MM:.0f} mm, this body must be >= "
      f"{feasible_w_mm/1000:.2f} m wide")

# overlay svg (green ok / red too tight), same viewBox
def seg(pts, rs):
    out = []
    for i in range(len(pts) - 1):
        bad = rs[i] < thr_svg or rs[i + 1] < thr_svg
        col = "#e6194b" if bad else "#1aaf5d"
        w = 3 if bad else 1.4
        out.append(f'<line x1="{pts[i][0]:.2f}" y1="{pts[i][1]:.2f}" '
                   f'x2="{pts[i+1][0]:.2f}" y2="{pts[i+1][1]:.2f}" stroke="{col}" stroke-width="{w}"/>')
    return "".join(out)

body = "".join(seg(pts, rs) for pts, rs in sampled)
(OUT / f"check_{name}.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.0f} {miny:.0f} {bw:.0f} {bh:.0f}">'
    f'<rect x="{minx:.0f}" y="{miny:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="#0e1116"/>{body}</svg>')

# paths.json in mm, canopy coords (centre origin, y up)
def to_mm(x, y):
    return [round((x - (minx + bw / 2)) * scale, 1), round(((miny + bh / 2) - y) * scale, 1)]
bodies = [{"name": f"{name}_{i}", "kind": "spline",
           "points": [to_mm(x, y) for x, y in pts], "color": "#ff7a1a"}
          for i, (pts, _rs) in enumerate(sampled)]
(OUT / f"{name}.paths.json").write_text(json.dumps(bodies, indent=1))
print(f"wrote out/check_{name}.svg  and  out/{name}.paths.json")
