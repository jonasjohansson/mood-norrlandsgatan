"""Bend-radius check + simplify for an LED-flex figure.

Reads an SVG body outline, SIMPLIFIES each path to a coarse anchor spacing (so the
tiny finger/face detail can't demand impossible bends), then computes the local
radius of curvature and flags anything tighter than the flex's min bend radius.
Writes:
  out/check_<name>.svg   overlay: green = OK, red = too tight
  out/<name>.paths.json  smoothed points (mm, canopy coords)
  out/paths.json         same, canonical name the rest of the pipeline reads

    cd cad && uv run --with svgpathtools python svgcheck.py "/path/Asset 1.svg" [width_mm] [simplify_mm]

width_mm    = how wide this body should be on the ceiling (default 4500)
simplify_mm = anchor spacing; larger = smoother/coarser (default 140)
"""
import sys, json, math
from pathlib import Path
from svgpathtools import svg2paths

MIN_BEND_MM = 90.0   # FN-ESJT-B0612 6x12 COB, assumed — confirm with supplier

src = Path(sys.argv[1])
target_w = float(sys.argv[2]) if len(sys.argv) > 2 else 4500.0
simplify_mm = float(sys.argv[3]) if len(sys.argv) > 3 else 140.0
name = src.stem.replace(" ", "_")
OUT = Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)

paths, _ = svg2paths(str(src))

def dense(path, step=1.2):
    L = path.length(); n = max(3, int(L / step))
    return [(z.real, z.imag) for z in (path.point(path.ilength(min(L, i/n*L))) for i in range(n+1))]

def resample(pts, N):
    if len(pts) < 2 or N < 2: return list(pts)
    cum = [0.0]
    for i in range(1, len(pts)): cum.append(cum[-1] + math.dist(pts[i], pts[i-1]))
    L = cum[-1] or 1.0; out = []; j = 0
    for i in range(N):
        d = L*i/(N-1)
        while j < len(pts)-2 and cum[j+1] < d: j += 1
        t = (d-cum[j])/((cum[j+1]-cum[j]) or 1)
        out.append((pts[j][0]+(pts[j+1][0]-pts[j][0])*t, pts[j][1]+(pts[j+1][1]-pts[j][1])*t))
    return out

def catmull(A, per=16):
    if len(A) < 3: return list(A)
    out = []
    for i in range(len(A)-1):
        p0=A[i-1] if i>0 else A[i]; p1=A[i]; p2=A[i+1]; p3=A[i+2] if i+2<len(A) else A[i+1]
        for k in range(per+1):
            t=k/per; t2=t*t; t3=t2*t
            out.append((0.5*(2*p1[0]+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3),
                        0.5*(2*p1[1]+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)))
    return out

def boxsmooth(pts, w, passes=2):
    if w < 2 or len(pts) < 3: return list(pts)
    h = w // 2
    for _ in range(passes):
        n = len(pts); out = []
        for i in range(n):
            a = max(0, i-h); b = min(n, i+h+1); c = b-a
            out.append((sum(p[0] for p in pts[a:b])/c, sum(p[1] for p in pts[a:b])/c))
        pts = out
    return pts

def circumR(a,b,c):
    A=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
    if A<1e-9: return math.inf
    return (math.dist(b,c)*math.dist(a,c)*math.dist(a,b))/(4*A)

# bbox + scale (svg units -> mm)
xs=[]; ys=[]
for p in paths:
    b=p.bbox(); xs+=[b[0],b[1]]; ys+=[b[2],b[3]]
minx,maxx,miny,maxy=min(xs),max(xs),min(ys),max(ys); bw,bh=maxx-minx,maxy-miny
scale=target_w/bw; simplify_svg=simplify_mm/scale; thr_svg=MIN_BEND_MM/scale

W=max(3, round(thr_svg/1.2*1.6))   # low-pass window ~ the min bend radius
curves=[]; minR=math.inf
for p in paths:
    d=boxsmooth(dense(p), W); N=max(4, round(p.length()/simplify_svg)); sm=catmull(resample(d,N))
    rs=[math.inf]+[circumR(sm[i-1],sm[i],sm[i+1]) for i in range(1,len(sm)-1)]+[math.inf]
    minR=min(minR, min(rs))
    curves.append((sm,rs))

tight=sum(1 for _,rs in curves for r in rs if r<thr_svg)
tot=sum(len(rs) for _,rs in curves)
total_m=sum(sum(math.dist(sm[i],sm[i+1]) for i in range(len(sm)-1)) for sm,_ in curves)*scale/1000

print(f"figure: {src.name}   paths: {len(paths)}   simplify: {simplify_mm:.0f} mm")
print(f"at {target_w:.0f} mm wide -> {target_w:.0f} x {bh*scale:.0f} mm   LED run {total_m:.1f} m")
print(f"tightest bend: {minR*scale:.0f} mm  (need >= {MIN_BEND_MM:.0f})   too tight: {tight}/{tot}")

def to_mm(x,y): return [round((x-(minx+bw/2))*scale,1), round(((miny+bh/2)-y)*scale,1)]
seg=lambda sm,rs:"".join(
    f'<line x1="{sm[i][0]:.1f}" y1="{sm[i][1]:.1f}" x2="{sm[i+1][0]:.1f}" y2="{sm[i+1][1]:.1f}" '
    f'stroke="{"#e6194b" if min(rs[i],rs[i+1])<thr_svg else "#1aaf5d"}" stroke-width="{3 if min(rs[i],rs[i+1])<thr_svg else 1.6}"/>'
    for i in range(len(sm)-1))
(OUT/f"check_{name}.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx:.0f} {miny:.0f} {bw:.0f} {bh:.0f}">'
    f'<rect x="{minx:.0f}" y="{miny:.0f}" width="{bw:.0f}" height="{bh:.0f}" fill="#0e1116"/>'
    + "".join(seg(sm,rs) for sm,rs in curves) + "</svg>")

bodies=[{"name":f"{name}_{i}","kind":"spline","points":[to_mm(x,y) for x,y in sm],"color":"#ff7a1a"}
        for i,(sm,_) in enumerate(curves)]
(OUT/f"{name}.paths.json").write_text(json.dumps(bodies,indent=1))
(OUT/"paths.json").write_text(json.dumps(bodies,indent=1))
print(f"wrote out/check_{name}.svg, out/{name}.paths.json and out/paths.json (pipeline)")
