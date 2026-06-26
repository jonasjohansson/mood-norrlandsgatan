"""Build one ceiling module: a back-plate panel + LED channels following the
figure / column paths, then export STL + STEP and a manifest.json the viewer reads.

    cd cad && uv run python figure.py

Paths below are STYLISED PLACEHOLDERS. Drop the real outlines in by exporting the
figures from `02 Design/2D/192 MOOD vN.ai` as SVG and converting node coords into
the (kind, points) lists in PATHS — the channel/neon geometry regenerates around them.
"""
import json
from pathlib import Path
from build123d import BuildSketch, RectangleRounded, Circle, extrude, Pos, export_stl, export_step

from channel import ChannelParams, path_line, walls, neon

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

P = ChannelParams()

# Prototype module footprint (mm). Real canopy is ~200 m^2, split into modules.
MW, MH = 1500.0, 1000.0
COLS = [(-300.0, 0.0, 120.0), (300.0, 0.0, 120.0)]  # the two entrance columns

# Stylised floating-figure strokes (placeholder splines) — replace from the .ai.
PATHS = [
    ("fig_a", "spline", [(-650, 280), (-480, 200), (-360, 300), (-470, 380), (-560, 300)],
     "#ff5a36"),
    ("fig_b", "spline", [(-120, -360), (40, -260), (180, -360), (60, -440), (-120, -360)],
     "#ff7a3c"),
    ("fig_c", "spline", [(420, 320), (560, 220), (660, 340), (540, 420), (420, 320)],
     "#ffd23f"),
    ("fig_d", "spline", [(-560, -120), (-360, -60), (-120, -140), (140, -40), (420, -160)],
     "#ff5a36"),
    ("ring_l", "circle", [COLS[0]], "#ff9f1c"),
    ("ring_r", "circle", [COLS[1]], "#ff9f1c"),
]


def back_plate():
    with BuildSketch() as sk:
        RectangleRounded(MW, MH, 90)
    panel = extrude(sk.sketch, amount=P.back_t)
    for cx, cy, r in COLS:                          # bore holes for the columns
        with BuildSketch(Pos(cx, cy, 0)) as h:
            Circle(r - 20)
        panel -= extrude(h.sketch, amount=P.back_t)
    return panel


def build():
    manifest = []

    # --- aluminium: back-plate + all return walls, one part ---
    alu = back_plate()
    for name, kind, pts, _color in PATHS:
        alu += walls(path_line(kind, pts), P)
    f = "panel.stl"
    export_stl(alu, str(OUT / f))
    export_step(alu, str(OUT / "panel.step"))
    manifest.append(dict(name="panel", file=f, color="#9aa0a6",
                         emissive=False, pos=[0, 0, 0], rot=[0, 0, 0]))

    # --- neon: one lit part per figure (toggle + glow in the viewer) ---
    for name, kind, pts, color in PATHS:
        tube = neon(path_line(kind, pts), P)
        f = f"{name}.stl"
        export_stl(tube, str(OUT / f))
        manifest.append(dict(name=name, file=f, color=color,
                             emissive=True, pos=[0, 0, 0], rot=[0, 0, 0]))

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {len(manifest)} parts + manifest.json to {OUT}")


if __name__ == "__main__":
    build()
