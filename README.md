# Mood Norrlandsgatan — "People in Orbit"

CAD + browser preview for the **AMF / Mood Gallerian** entrance light installation
(Norrlandsgatan, Stockholm). Replaces Peter Hagdahl's *Liquid Sky*. Concept:
glowing human-like bodies made of **silicone neon-flex**, pushed into a **glossy
snap-groove host** that is bracketed to the **existing ceiling steel profiles**.

Brief: ceiling-mounted, light-bearing, weather-resistant, 10-year life, 3 m
clearance, fire (PBL — bygglov granted). Canopy ≈ **9 × 5 m**.

## The neon — FN-ESJT-B1023 "Full Black Side", 10 × 23 mm
Dome-emitting silicone neon-flex: light comes only from the rounded dome (sides
blacked out → one clean glowing line). The host grips the **10 mm foot**; the
**23 mm body + dome hang down**, dome facing the room.

## The engineering
```
  existing steel profile  ═══════════════════   (you bolt the bracket here)
           │ bracket
  ┌────────┴───────────────────────────────┐
  │  GLOSSY HOST PANEL                       │
  │     ╲__╱  dovetail groove (undercut)     │   foot snaps past the lip,
  └───────┐██┌───────────────────────────────┘   can't drop out overhead
          ██ body + dome hang down, light into the room
```
The **undercut groove** (narrow mouth, wider inside) lets the squishy foot snap in
and stay put overhead — no clips, no glue. See it in `detail.py` (assemble/explode
in the viewer).

## Layout
```
cad/
  channel.py    # core: HostParams (real FN-ESJT-B1023 dims), snap-groove, neon, coupon
  detail.py     # ENGINEERING detail: dovetail snap + bracket + steel profile (the part to ideate)
  figure.py     # full 9x5 m canopy module -> STL/STEP + manifest (reads paths.json if present)
  calibrate.py  # neon snap-fit coupons across slot clearances (print/cut & tune)
  render.py     # headless STL -> PNG
  index.html    # light, static 3D viewer: toggles + explode (the active tool)
  ideate.html   # optional: freehand pattern sketcher (not needed — bodies come from the .ai)
  out/          # exported .stl/.step + manifest.json  (gitignored)
```
`out/` and `.venv/` are gitignored — the `.py` files are the source of truth.

## Use
```sh
cd cad
uv run python detail.py        # engineering detail (snap + steel connection)
#   or: uv run python figure.py    full canopy
python3 -m http.server 8000    # open http://localhost:8000/cad/  (explode to inspect)
uv run python calibrate.py     # snap-fit coupons to print/cut and tune the push-fit
```
Whichever script you run last writes `out/manifest.json`, which the viewer reads.

## Parameters (`cad/channel.py` → `HostParams`, mm)
| param | default | meaning |
|---|---|---|
| `neon_w` / `neon_h` | 10 / 23 | FN-ESJT-B1023 foot width / full height |
| `foot` | 6 | depth of the foot gripped in the groove |
| `slot_clr` | 0.4 | per-side push-fit clearance — **tune with `calibrate.py`** |
| `slot_depth` | 6 | groove depth |
| `lip` | 1.4 | undercut retaining lip per side (dovetail bit) |
| `panel_t` | 12 | glossy host thickness |

## Bodies
The human figures exist as vector paths in `02 Design/2D/192 MOOD v*.ai` (black =
neon centerline). Next: extract those paths → `paths.json` → `figure.py` draws the
real bodies into the canopy. (`ideate.html` can hand-draw extras if ever needed.)

## Next
- [ ] Extract the `.ai` human centerlines → `paths.json` (the real bodies).
- [ ] Confirm FN-ESJT-B1023 mounting foot geometry against its datasheet; refine the groove section + `lip`.
- [ ] Real steel-profile section/spacing from site → bracket type (channel-nut vs L).
- [ ] Sweep the undercut groove along curved paths (today it's exact only on the straight detail/coupon).
- [ ] Split the 9 × 5 m host into transport/install modules; match the faceted soffit.
