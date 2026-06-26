# Mood Norrlandsgatan — ceiling artwork prototype

Code-CAD + browser prototype for the **AMF / Mood Gallerian** entrance light
installation (Norrlandsgatan, Stockholm). Replaces Peter Hagdahl's *Liquid Sky*;
brief calls for a ceiling-mounted, light-bearing, weather-resistant work with a
**10-year** lifespan, 3 m clearance, fire compliance (PBL — bygglov granted).

The piece is built as **channel-letter trays**: a flat aluminium back-plate with
return walls bent on edge along the figure paths, **silicone LED neon-flex** seated
in the slot, light facing down. The walls are the heatsink + the matte surround.

## Layout
```
cad/
  channel.py     # core parametric U-channel (cross-section + sweep) + test coupon
  figure.py      # one ceiling module: back-plate + channels -> STL/STEP + manifest.json
  calibrate.py   # neon snap-fit coupons across slot clearances (tune before committing)
  render.py      # headless STL -> PNG preview
  index.html     # Three.js viewer (toggles, explode, bloom glow) — reads out/manifest.json
  out/           # exported .stl/.step + manifest.json  (gitignored)
```
`out/` and `.venv/` are gitignored — the `.py` files are the source of truth.

## Build & review
```sh
cd cad
uv run python figure.py        # generate the module + manifest.json
uv run python calibrate.py     # (optional) neon fit coupons
python3 -m http.server 8000    # then open http://localhost:8000/cad/
```
Viewer: per-part toggles, **explode** (drops the neon out of the channel mouth),
**glow** (bloom), and a *view-from-below* button (how you'll actually see it).

## Parameters (`cad/channel.py` → `ChannelParams`)
| param | default | meaning |
|---|---|---|
| `neon_w` / `neon_h` | 16 / 16 mm | silicone neon-flex cross-section |
| `wall_t` | 2 mm | aluminium return-wall thickness |
| `wall_h` | 10 mm | wall shielding height above the neon face |
| `back_t` | 3 mm | back-plate thickness |
| `slot_clr` | 0.4 mm | per-side snap clearance — **tune with `calibrate.py`** |

## Status / next
- [x] Parametric channel + neon + back-plate module, STL/STEP export, viewer.
- [ ] Replace placeholder splines in `figure.py:PATHS` with the real figure
      outlines (export `02 Design/2D/192 MOOD vN.ai` → SVG → node coords).
- [ ] Split the canopy into transport/install modules; add suspension tabs.
- [ ] Confirm a real neon-flex product (IP65+, fire class) and back its datasheet.
- [ ] Add lead-in/lip detail to the channel mouth; fillet wall roots.
